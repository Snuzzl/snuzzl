from types import SimpleNamespace

import pytest

import app.managers.reward_manager as reward_manager_module
from app.managers.reward_manager import RewardManager


class _DummyDB:
    def __init__(self, existing=None):
        self._existing = existing if existing is not None else {}
        self.created = None
        self.updated = None
        self.deleted = None

    def create_record(self, model, **kwargs):
        self.created = (model, kwargs)
        return SimpleNamespace(reward_id=1, **kwargs)

    def read_record(self, model, *keys):
        return self._existing.get((model, *keys))

    def update_record(self, model, key, **kwargs):
        self.updated = (model, key, kwargs)
        return 1

    def delete_record(self, model, key):
        self.deleted = (model, key)
        return 1


class _FakeDeleteRow:
    def __init__(self):
        self.deleted = False

    def delete_instance(self):
        self.deleted = True


class _FakeUpdateQuery:
    def __init__(self, execute_result=0):
        self.execute_result = execute_result
        self.where_called = False

    def where(self, *_args, **_kwargs):
        self.where_called = True
        return self

    def execute(self):
        return self.execute_result


def test_require_db_raises_when_not_configured():
    manager = RewardManager(database_manager=None)
    with pytest.raises(RuntimeError, match="not configured"):
        manager._require_db()


def test_validate_reward_name_rejects_invalid_values():
    manager = RewardManager(database_manager=object())

    with pytest.raises(ValueError, match="non-empty"):
        manager._validate_reward_name("")

    with pytest.raises(ValueError, match="cannot exceed"):
        manager._validate_reward_name("x" * 51)


def test_normalize_reward_ids_variants():
    manager = RewardManager(database_manager=object())

    assert manager._normalize_reward_ids(None) is None
    assert manager._normalize_reward_ids(7) == [7]
    assert manager._normalize_reward_ids(["1", 2]) == [1, 2]


def test_create_reward_requires_dict_and_required_fields():
    manager = RewardManager(database_manager=_DummyDB())

    with pytest.raises(TypeError, match="data must be a dict"):
        manager.create_reward("bad")

    with pytest.raises(ValueError, match="Missing reward fields"):
        manager.create_reward({"chall_id": 1})


def test_create_reward_creates_record_when_valid(monkeypatch):
    db = _DummyDB()
    manager = RewardManager(database_manager=db)

    monkeypatch.setattr(manager, "_require_existing_challenge", lambda _challenge_id: None)
    monkeypatch.setattr(manager, "_require_existing_reward_type", lambda _reward_type_id: None)

    created = manager.create_reward({"chall_id": 10, "reward_name": "Gold Badge", "reward_type": 2})

    assert created.reward_id == 1
    assert db.created is not None
    model, kwargs = db.created
    assert model is reward_manager_module.Rewards
    assert kwargs == {"chall_id": 10, "reward_name": "Gold Badge", "reward_type": 2}


def test_get_reward_delegates_to_db_read_record():
    existing = {(reward_manager_module.Rewards, 9): SimpleNamespace(reward_id=9)}
    manager = RewardManager(database_manager=_DummyDB(existing=existing))

    row = manager.get_reward(9)
    assert row.reward_id == 9


def test_update_reward_validates_input_and_returns_zero_for_no_payload_or_missing_row():
    db = _DummyDB(existing={})
    manager = RewardManager(database_manager=db)

    with pytest.raises(TypeError, match="data must be a dict"):
        manager.update_reward("bad")

    with pytest.raises(ValueError, match="Missing reward_id"):
        manager.update_reward({"reward_name": "Name"})

    assert manager.update_reward({"reward_id": 1, "unknown": "x"}) == 0
    assert manager.update_reward({"reward_id": 1, "reward_name": "Name"}) == 0


def test_update_reward_updates_existing_record(monkeypatch):
    existing = {(reward_manager_module.Rewards, 5): SimpleNamespace(reward_id=5)}
    db = _DummyDB(existing=existing)
    manager = RewardManager(database_manager=db)

    monkeypatch.setattr(manager, "_require_existing_challenge", lambda _challenge_id: None)
    monkeypatch.setattr(manager, "_require_existing_reward_type", lambda _reward_type_id: None)

    result = manager.update_reward({"reward_id": 5, "reward_name": "New Name", "chall_id": 2, "reward_type": 1})

    assert result == 1
    assert db.updated == (
        reward_manager_module.Rewards,
        5,
        {"reward_name": "New Name", "chall_id": 2, "reward_type": 1},
    )


def test_delete_reward_returns_zero_for_missing_and_deletes_when_present():
    missing_manager = RewardManager(database_manager=_DummyDB(existing={}))
    assert missing_manager.delete_reward(1) == 0

    existing = {(reward_manager_module.Rewards, 2): SimpleNamespace(reward_id=2)}
    db = _DummyDB(existing=existing)
    manager = RewardManager(database_manager=db)

    assert manager.delete_reward(2) == 1
    assert db.deleted == (reward_manager_module.Rewards, 2)


def test_claim_reward_raises_for_missing_reward():
    manager = RewardManager(database_manager=_DummyDB(existing={}))

    with pytest.raises(ValueError, match="reward_id does not exist"):
        manager.claim_reward(user_id=1, reward_id=999)


def test_claim_reward_unclaims_when_existing(monkeypatch):
    existing = {(reward_manager_module.Rewards, 5): SimpleNamespace(reward_id=5)}
    manager = RewardManager(database_manager=_DummyDB(existing=existing))
    row = _FakeDeleteRow()

    monkeypatch.setattr(reward_manager_module.UserRewards, "get_or_none", lambda *_args, **_kwargs: row)

    assert manager.claim_reward(user_id=1, reward_id=5) is False
    assert row.deleted is True


def test_claim_reward_creates_when_not_existing(monkeypatch):
    existing = {(reward_manager_module.Rewards, 5): SimpleNamespace(reward_id=5)}
    manager = RewardManager(database_manager=_DummyDB(existing=existing))
    created = []

    monkeypatch.setattr(reward_manager_module.UserRewards, "get_or_none", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(
        reward_manager_module.UserRewards,
        "create",
        lambda **kwargs: created.append(kwargs) or SimpleNamespace(**kwargs),
    )

    assert manager.claim_reward(user_id=7, reward_id=5, status="Complete") is True
    assert created == [{"user_id": 7, "reward_id": 5, "reward_status": "Complete"}]


def test_award_challenge_rewards_skips_existing_and_awards_new(monkeypatch):
    manager = RewardManager(database_manager=object())
    rewards = [SimpleNamespace(reward_id=10), SimpleNamespace(reward_id=11)]
    created = []

    class _RewardChain:
        def __init__(self, rows):
            self.rows = rows

        def where(self, *_args, **_kwargs):
            return self.rows

    monkeypatch.setattr(manager, "_require_existing_challenge", lambda _challenge_id: None)
    monkeypatch.setattr(reward_manager_module.Rewards, "select", lambda *_args, **_kwargs: _RewardChain(rewards))
    monkeypatch.setattr(
        reward_manager_module.UserRewards,
        "get_or_none",
        lambda *_args, **_kwargs: SimpleNamespace() if _args else None,
    )

    def _fake_get_or_none(*args, **_kwargs):
        _ = args
        return None if len(created) == 0 else SimpleNamespace()

    monkeypatch.setattr(reward_manager_module.UserRewards, "get_or_none", _fake_get_or_none)
    monkeypatch.setattr(
        reward_manager_module.UserRewards,
        "create",
        lambda **kwargs: created.append(kwargs) or SimpleNamespace(**kwargs),
    )

    awarded = manager.award_challenge_rewards(user_id=1, challenge_id=7, status="Complete")

    assert awarded == 1
    assert created == [{"user_id": 1, "reward_id": 10, "reward_status": "Complete"}]


def test_update_user_rewards_handles_empty_and_invalid_target_ids(monkeypatch):
    manager = RewardManager(database_manager=object())

    with pytest.raises(ValueError, match="non-empty"):
        manager.update_user_rewards(user_id=1, reward_name="   ")

    monkeypatch.setattr(manager, "view_user_rewards", lambda _user_id: [SimpleNamespace(reward_id=1)])

    with pytest.raises(ValueError, match="not linked"):
        manager.update_user_rewards(user_id=1, reward_ids=[1, 999], reward_name="Gold")


def test_update_user_rewards_updates_selected_ids(monkeypatch):
    manager = RewardManager(database_manager=object())
    query = _FakeUpdateQuery(execute_result=2)

    monkeypatch.setattr(manager, "view_user_rewards", lambda _user_id: [SimpleNamespace(reward_id=1), SimpleNamespace(reward_id=2)])
    monkeypatch.setattr(reward_manager_module.Rewards, "update", lambda **_payload: query)
    monkeypatch.setattr(manager, "_require_existing_reward_type", lambda _type_id: None)

    result = manager.update_user_rewards(user_id=7, reward_ids=[1, 2], reward_type=1)

    assert result == 2
    assert query.where_called is True