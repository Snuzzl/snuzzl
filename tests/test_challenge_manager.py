from datetime import date, timedelta
from types import SimpleNamespace

import pytest

import app.managers.challenge_manager as challenge_manager_module
from app.managers.challenge_manager import ChallengeManager


class _DummyDB:
    def __init__(self, existing=None):
        self._existing = existing if existing is not None else {}
        self.created = None
        self.deleted = None

    def read_record(self, model, *keys):
        return self._existing.get((model, *keys))

    def create_record(self, model, **kwargs):
        self.created = (model, kwargs)
        return SimpleNamespace(chall_id_id=kwargs["chall_id"], chall_sdate=kwargs["chall_sdate"], chall_edate=kwargs["chall_edate"])

    def delete_record(self, model, key_tuple):
        self.deleted = (model, key_tuple)


class _ExistsQuery:
    def __init__(self, exists_value):
        self._exists_value = exists_value

    def join(self, *args, **kwargs):
        return self

    def where(self, *args, **kwargs):
        return self

    def exists(self):
        return self._exists_value


class _FakeChain:
    def __init__(self, rows):
        self._rows = rows

    def join(self, *args, **kwargs):
        return self

    def where(self, *args, **kwargs):
        return self

    def order_by(self, *args, **kwargs):
        return self

    def __iter__(self):
        return iter(self._rows)


def test_require_db_raises_when_not_configured():
    manager = ChallengeManager(db=None)
    with pytest.raises(RuntimeError, match="not configured"):
        manager._require_db()


def test_parse_date_accepts_iso_string_and_date_instance():
    manager = ChallengeManager(db=object())
    assert manager._parse_date("2026-05-11", "chall_sdate") == date(2026, 5, 11)
    assert manager._parse_date(date(2026, 5, 12), "chall_sdate") == date(2026, 5, 12)


def test_parse_date_accepts_none():
    manager = ChallengeManager(db=object())
    assert manager._parse_date(None, "chall_sdate") is None


def test_parse_date_rejects_invalid_values():
    manager = ChallengeManager(db=object())

    with pytest.raises(ValueError, match="chall_sdate must be YYYY-MM-DD"):
        manager._parse_date("11/05/2026", "chall_sdate")

    with pytest.raises(ValueError, match="chall_sdate must be YYYY-MM-DD"):
        manager._parse_date(123, "chall_sdate")


def test_require_existing_challenge_raises_for_missing_challenge():
    db = _DummyDB(existing={})
    manager = ChallengeManager(db=db)

    with pytest.raises(ValueError, match="chall_id does not exist"):
        manager._require_existing_challenge(99)


def test_require_existing_challenge_passes_when_present():
    db = _DummyDB(existing={(challenge_manager_module.Challenges, 7): SimpleNamespace(chall_id=7)})
    manager = ChallengeManager(db=db)

    manager._require_existing_challenge(7)


def test_join_challenge_uses_default_dates_when_not_provided(monkeypatch):
    db = _DummyDB(existing={(challenge_manager_module.Challenges, 7): SimpleNamespace(chall_id=7)})
    manager = ChallengeManager(db=db)

    row = manager.join_challenge(user_id=5, chall_id=7)

    assert row.chall_id_id == 7
    assert db.created is not None
    created_model, created_kwargs = db.created
    assert created_model is challenge_manager_module.UserChallenges
    assert created_kwargs["chall_sdate"] == date.today()
    assert created_kwargs["chall_edate"] == date.today() + timedelta(days=7)


def test_join_challenge_rejects_duplicate_enrollment():
    existing_map = {
        (challenge_manager_module.Challenges, 7): SimpleNamespace(chall_id=7),
        (challenge_manager_module.UserChallenges, 5, 7): SimpleNamespace(user_id=5, chall_id_id=7),
    }
    manager = ChallengeManager(db=_DummyDB(existing=existing_map))

    with pytest.raises(ValueError, match="already enrolled"):
        manager.join_challenge(user_id=5, chall_id=7)


def test_join_challenge_rejects_end_date_before_start_date():
    existing_map = {(challenge_manager_module.Challenges, 7): SimpleNamespace(chall_id=7)}
    manager = ChallengeManager(db=_DummyDB(existing=existing_map))

    with pytest.raises(ValueError, match="on or after"):
        manager.join_challenge(user_id=5, chall_id=7, chall_sdate="2026-05-20", chall_edate="2026-05-10")


def test_leave_challenge_deletes_existing_enrollment():
    existing_map = {(challenge_manager_module.UserChallenges, 5, 7): SimpleNamespace(user_id=5, chall_id_id=7)}
    db = _DummyDB(existing=existing_map)
    manager = ChallengeManager(db=db)

    result = manager.leave_challenge(user_id=5, chall_id=7)

    assert result is True
    assert db.deleted == (challenge_manager_module.UserChallenges, (5, 7))


def test_leave_challenge_rejects_missing_enrollment():
    manager = ChallengeManager(db=_DummyDB(existing={}))

    with pytest.raises(ValueError, match="not enrolled"):
        manager.leave_challenge(user_id=5, chall_id=7)


def test_user_challenge_status_completed_when_reward_already_awarded(monkeypatch):
    manager = ChallengeManager(db=object())

    monkeypatch.setattr(challenge_manager_module.UserRewards, "select", lambda *args, **kwargs: _ExistsQuery(True))
    monkeypatch.setattr(manager, "get_required_task_progress", lambda *args, **kwargs: {"required_total": 1, "completed_total": 0})

    status = manager.get_user_challenge_status(user_id=1, chall_id=2, chall_edate=date(2099, 1, 1))
    assert status == "completed"


def test_user_challenge_status_completed_when_progress_full(monkeypatch):
    manager = ChallengeManager(db=object())

    monkeypatch.setattr(challenge_manager_module.UserRewards, "select", lambda *args, **kwargs: _ExistsQuery(False))
    monkeypatch.setattr(manager, "get_required_task_progress", lambda *args, **kwargs: {"required_total": 2, "completed_total": 2})

    status = manager.get_user_challenge_status(user_id=1, chall_id=2, chall_edate=date(2099, 1, 1))
    assert status == "completed"


def test_user_challenge_status_failed_after_end_date(monkeypatch):
    manager = ChallengeManager(db=object())

    monkeypatch.setattr(challenge_manager_module.UserRewards, "select", lambda *args, **kwargs: _ExistsQuery(False))
    monkeypatch.setattr(manager, "get_required_task_progress", lambda *args, **kwargs: {"required_total": 2, "completed_total": 1})

    status = manager.get_user_challenge_status(user_id=1, chall_id=2, chall_edate=date(2000, 1, 1))
    assert status == "failed"


def test_user_challenge_status_active_when_not_completed_and_not_expired(monkeypatch):
    manager = ChallengeManager(db=object())

    monkeypatch.setattr(challenge_manager_module.UserRewards, "select", lambda *args, **kwargs: _ExistsQuery(False))
    monkeypatch.setattr(manager, "get_required_task_progress", lambda *args, **kwargs: {"required_total": 2, "completed_total": 1})

    status = manager.get_user_challenge_status(user_id=1, chall_id=2, chall_edate=date(2099, 1, 1))
    assert status == "active"


def test_user_challenge_status_failed_when_no_required_tasks_and_expired(monkeypatch):
    manager = ChallengeManager(db=object())

    monkeypatch.setattr(challenge_manager_module.UserRewards, "select", lambda *args, **kwargs: _ExistsQuery(False))
    monkeypatch.setattr(manager, "get_required_task_progress", lambda *args, **kwargs: {"required_total": 0, "completed_total": 0})

    status = manager.get_user_challenge_status(user_id=1, chall_id=2, chall_edate=date(2000, 1, 1))
    assert status == "failed"


def test_get_all_challenges_returns_rows(monkeypatch):
    manager = ChallengeManager(db=object())
    rows = [SimpleNamespace(chall_id=1), SimpleNamespace(chall_id=2)]

    monkeypatch.setattr(challenge_manager_module.Challenges, "select", lambda *args, **kwargs: rows)

    result = manager.get_all_challenges()
    assert [row.chall_id for row in result] == [1, 2]


def test_get_user_challenges_returns_joined_rows(monkeypatch):
    manager = ChallengeManager(db=object())
    rows = [SimpleNamespace(user_id=5, chall_id=SimpleNamespace(chall_id=7))]

    monkeypatch.setattr(challenge_manager_module.UserChallenges, "select", lambda *args, **kwargs: _FakeChain(rows))

    result = manager.get_user_challenges(user_id=5)
    assert len(result) == 1
    assert result[0].chall_id.chall_id == 7


def test_get_required_task_progress_returns_zeroes_when_no_required_tasks(monkeypatch):
    manager = ChallengeManager(db=object())

    monkeypatch.setattr(manager, "_require_existing_challenge", lambda chall_id: None)
    monkeypatch.setattr(challenge_manager_module.Tasks, "select", lambda *args, **kwargs: _FakeChain([]))

    progress = manager.get_required_task_progress(user_id=5, chall_id=7)

    assert progress == {
        "required_total": 0,
        "completed_total": 0,
        "completed_task_ids": [],
        "pending_task_ids": [],
        "completion_ratio": 0.0,
    }


def test_get_required_task_summary_returns_default_when_no_tasks(monkeypatch):
    manager = ChallengeManager(db=object())

    monkeypatch.setattr(manager, "_require_existing_challenge", lambda chall_id: None)
    monkeypatch.setattr(challenge_manager_module.Tasks, "select", lambda *args, **kwargs: _FakeChain([]))

    summary = manager.get_required_task_summary(chall_id=7)

    assert summary == {
        "count": 0,
        "summary": "no required tasks configured",
        "by_type": {},
        "task_ids": [],
        "task_names": [],
    }


def test_get_required_task_summary_builds_type_counts_and_summary(monkeypatch):
    manager = ChallengeManager(db=object())
    rows = [
        SimpleNamespace(task_id=1, task_name="Run", type_id=SimpleNamespace(type_name="Exercise")),
        SimpleNamespace(task_id=2, task_name="Hydrate", type_id=SimpleNamespace(type_name="Health")),
        SimpleNamespace(task_id=3, task_name="Walk", type_id=SimpleNamespace(type_name="Exercise")),
    ]

    monkeypatch.setattr(manager, "_require_existing_challenge", lambda chall_id: None)
    monkeypatch.setattr(challenge_manager_module.Tasks, "select", lambda *args, **kwargs: _FakeChain(rows))

    summary = manager.get_required_task_summary(chall_id=7)

    assert summary["count"] == 3
    assert summary["by_type"] == {"Exercise": 2, "Health": 1}
    assert summary["task_ids"] == [1, 2, 3]
    assert summary["task_names"] == ["Run", "Hydrate", "Walk"]
    assert summary["summary"] == "do 2 exercise tasks, 1 health task"


def test_get_required_tasks_for_user_returns_empty_when_no_required_links(monkeypatch):
    manager = ChallengeManager(db=object())

    monkeypatch.setattr(manager, "_require_existing_challenge", lambda chall_id: None)
    monkeypatch.setattr(challenge_manager_module.TaskChallenges, "select", lambda *args, **kwargs: _FakeChain([]))

    result = manager.get_required_tasks_for_user(user_id=5, chall_id=7)
    assert result == []


def test_join_challenge_accepts_explicit_iso_dates():
    db = _DummyDB(existing={(challenge_manager_module.Challenges, 7): SimpleNamespace(chall_id=7)})
    manager = ChallengeManager(db=db)

    row = manager.join_challenge(user_id=5, chall_id=7, chall_sdate="2026-05-01", chall_edate="2026-05-12")

    assert row.chall_sdate == date(2026, 5, 1)
    assert row.chall_edate == date(2026, 5, 12)


def test_get_required_tasks_for_user_maps_assigned_and_fallback_fields(monkeypatch):
    manager = ChallengeManager(db=object())

    required_links = [
        SimpleNamespace(task_id_id=1),
        SimpleNamespace(task_id_id=2),
        SimpleNamespace(task_id_id=2),
        SimpleNamespace(task_id_id=3),
    ]
    task_rows = [
        SimpleNamespace(task_id=1, task_name="Run", task_desc="Cardio", type_id=SimpleNamespace(type_name="Exercise")),
        SimpleNamespace(task_id=2, task_name="Read", task_desc="Book", type_id=SimpleNamespace(type_name="Mindfulness")),
    ]
    assigned_rows = [
        SimpleNamespace(task_id_id=1, task_complete=True),
        SimpleNamespace(task_id_id=3, task_complete=False),
    ]

    monkeypatch.setattr(manager, "_require_existing_challenge", lambda chall_id: None)
    monkeypatch.setattr(challenge_manager_module.TaskChallenges, "select", lambda *args, **kwargs: _FakeChain(required_links))
    monkeypatch.setattr(challenge_manager_module.Tasks, "select", lambda *args, **kwargs: _FakeChain(task_rows))
    monkeypatch.setattr(challenge_manager_module.UserTask, "select", lambda *args, **kwargs: _FakeChain(assigned_rows))

    result = manager.get_required_tasks_for_user(user_id=5, chall_id=7)

    assert [row["task_id"] for row in result] == [1, 2, 3]
    assert result[0]["task_name"] == "Run"
    assert result[0]["assigned"] is True
    assert result[0]["completed"] is True
    assert result[1]["assigned"] is False
    assert result[1]["completed"] is False
    assert result[2]["task_name"] == "task #3"
    assert result[2]["type_name"] == "unknown"
    assert result[2]["assigned"] is True
    assert result[2]["completed"] is False


def test_get_required_task_progress_counts_by_type_across_predefined_and_custom(monkeypatch):
    manager = ChallengeManager(db=object())

    required_rows = [
        SimpleNamespace(task_id=10, type_id_id=1),
        SimpleNamespace(task_id=11, type_id_id=1),
        SimpleNamespace(task_id=12, type_id_id=2),
    ]
    direct_completed_rows = [SimpleNamespace(task_id_id=10)]
    predefined_rows = [
        SimpleNamespace(task_id=SimpleNamespace(type_id_id=1)),
        SimpleNamespace(task_id=SimpleNamespace(type_id_id=2)),
    ]
    custom_rows = [SimpleNamespace(cust_id=SimpleNamespace(type_id_id=1))]

    monkeypatch.setattr(manager, "_require_existing_challenge", lambda chall_id: None)
    monkeypatch.setattr(challenge_manager_module.Tasks, "select", lambda *args, **kwargs: _FakeChain(required_rows))

    def _select_user_task(*args, **kwargs):
        if len(args) == 1:
            return _FakeChain(direct_completed_rows)
        if len(args) == 2 and args[0] is challenge_manager_module.UserTask.task_id:
            return _FakeChain(predefined_rows)
        if len(args) == 2 and args[0] is challenge_manager_module.UserTask.cust_id:
            return _FakeChain(custom_rows)
        raise AssertionError("Unexpected UserTask.select signature")

    monkeypatch.setattr(challenge_manager_module.UserTask, "select", _select_user_task)

    progress = manager.get_required_task_progress(user_id=5, chall_id=7)

    assert progress["required_total"] == 3
    assert progress["completed_total"] == 3
    assert progress["completed_task_ids"] == [10]
    assert progress["pending_task_ids"] == [11, 12]
    assert progress["completion_ratio"] == 1.0


def test_get_required_task_progress_uses_minimum_per_required_type(monkeypatch):
    manager = ChallengeManager(db=object())

    required_rows = [
        SimpleNamespace(task_id=10, type_id_id=1),
        SimpleNamespace(task_id=11, type_id_id=1),
        SimpleNamespace(task_id=12, type_id_id=2),
    ]
    direct_completed_rows = [SimpleNamespace(task_id_id=10)]
    predefined_rows = [SimpleNamespace(task_id=SimpleNamespace(type_id_id=1))]
    custom_rows = []

    monkeypatch.setattr(manager, "_require_existing_challenge", lambda chall_id: None)
    monkeypatch.setattr(challenge_manager_module.Tasks, "select", lambda *args, **kwargs: _FakeChain(required_rows))

    def _select_user_task(*args, **kwargs):
        if len(args) == 1:
            return _FakeChain(direct_completed_rows)
        if len(args) == 2 and args[0] is challenge_manager_module.UserTask.task_id:
            return _FakeChain(predefined_rows)
        if len(args) == 2 and args[0] is challenge_manager_module.UserTask.cust_id:
            return _FakeChain(custom_rows)
        raise AssertionError("Unexpected UserTask.select signature")

    monkeypatch.setattr(challenge_manager_module.UserTask, "select", _select_user_task)

    progress = manager.get_required_task_progress(user_id=5, chall_id=7)

    assert progress["required_total"] == 3
    assert progress["completed_total"] == 1
    assert progress["completion_ratio"] == (1 / 3)
    assert progress["completed_task_ids"] == [10]
    assert progress["pending_task_ids"] == [11, 12]


def test_get_required_task_progress_ignores_none_direct_task_ids(monkeypatch):
    manager = ChallengeManager(db=object())

    required_rows = [SimpleNamespace(task_id=10, type_id_id=1)]
    direct_completed_rows = [SimpleNamespace(task_id_id=None), SimpleNamespace(task_id_id=10)]
    predefined_rows = [SimpleNamespace(task_id=SimpleNamespace(type_id_id=1))]
    custom_rows = []

    monkeypatch.setattr(manager, "_require_existing_challenge", lambda chall_id: None)
    monkeypatch.setattr(challenge_manager_module.Tasks, "select", lambda *args, **kwargs: _FakeChain(required_rows))

    def _select_user_task(*args, **kwargs):
        if len(args) == 1:
            return _FakeChain(direct_completed_rows)
        if len(args) == 2 and args[0] is challenge_manager_module.UserTask.task_id:
            return _FakeChain(predefined_rows)
        if len(args) == 2 and args[0] is challenge_manager_module.UserTask.cust_id:
            return _FakeChain(custom_rows)
        raise AssertionError("Unexpected UserTask.select signature")

    monkeypatch.setattr(challenge_manager_module.UserTask, "select", _select_user_task)

    progress = manager.get_required_task_progress(user_id=5, chall_id=7)

    assert progress["completed_task_ids"] == [10]
    assert progress["pending_task_ids"] == []


def test_get_required_task_progress_caps_completed_total_at_required(monkeypatch):
    manager = ChallengeManager(db=object())

    required_rows = [
        SimpleNamespace(task_id=10, type_id_id=1),
        SimpleNamespace(task_id=11, type_id_id=1),
    ]
    direct_completed_rows = [SimpleNamespace(task_id_id=10), SimpleNamespace(task_id_id=11)]
    predefined_rows = [
        SimpleNamespace(task_id=SimpleNamespace(type_id_id=1)),
        SimpleNamespace(task_id=SimpleNamespace(type_id_id=1)),
        SimpleNamespace(task_id=SimpleNamespace(type_id_id=1)),
    ]
    custom_rows = [SimpleNamespace(cust_id=SimpleNamespace(type_id_id=1))]

    monkeypatch.setattr(manager, "_require_existing_challenge", lambda chall_id: None)
    monkeypatch.setattr(challenge_manager_module.Tasks, "select", lambda *args, **kwargs: _FakeChain(required_rows))

    def _select_user_task(*args, **kwargs):
        if len(args) == 1:
            return _FakeChain(direct_completed_rows)
        if len(args) == 2 and args[0] is challenge_manager_module.UserTask.task_id:
            return _FakeChain(predefined_rows)
        if len(args) == 2 and args[0] is challenge_manager_module.UserTask.cust_id:
            return _FakeChain(custom_rows)
        raise AssertionError("Unexpected UserTask.select signature")

    monkeypatch.setattr(challenge_manager_module.UserTask, "select", _select_user_task)

    progress = manager.get_required_task_progress(user_id=5, chall_id=7)

    assert progress["required_total"] == 2
    assert progress["completed_total"] == 2
    assert progress["completion_ratio"] == 1.0


def test_join_challenge_accepts_date_objects_directly():
    db = _DummyDB(existing={(challenge_manager_module.Challenges, 7): SimpleNamespace(chall_id=7)})
    manager = ChallengeManager(db=db)

    row = manager.join_challenge(user_id=5, chall_id=7, chall_sdate=date(2026, 5, 1), chall_edate=date(2026, 5, 12))

    assert row.chall_sdate == date(2026, 5, 1)
    assert row.chall_edate == date(2026, 5, 12)


def test_join_challenge_default_end_date_uses_given_start_date():
    db = _DummyDB(existing={(challenge_manager_module.Challenges, 7): SimpleNamespace(chall_id=7)})
    manager = ChallengeManager(db=db)

    row = manager.join_challenge(user_id=5, chall_id=7, chall_sdate="2026-05-10")

    assert row.chall_sdate == date(2026, 5, 10)
    assert row.chall_edate == date(2026, 5, 17)


def test_get_required_task_summary_uses_singular_label_for_one_task(monkeypatch):
    manager = ChallengeManager(db=object())
    rows = [
        SimpleNamespace(task_id=1, task_name="Run", type_id=SimpleNamespace(type_name="Exercise")),
    ]

    monkeypatch.setattr(manager, "_require_existing_challenge", lambda chall_id: None)
    monkeypatch.setattr(challenge_manager_module.Tasks, "select", lambda *args, **kwargs: _FakeChain(rows))

    summary = manager.get_required_task_summary(chall_id=7)

    assert summary["count"] == 1
    assert summary["summary"] == "do 1 exercise task"
