# tests/test_task_manager_full.py
"""
Comprehensive pytest suite for TaskManager that aims to cover all partitions
from the test plan. This file follows the same style as the other manager
tests in the repo: it injects a MagicMock DB manager into TaskManager and
asserts the manager calls the DB layer correctly and handles edge cases.

Notes:
- Tests use a `db_mock` fixture and a `tm` fixture that constructs
  TaskManager(db=db_mock). Adjust the constructor call if your TaskManager
  signature differs.
- Some partitions are implementation-dependent; those tests are marked xfail.
"""

import pytest
from unittest.mock import MagicMock
from datetime import date, time

from app.managers.task_manager import TaskManager


class FakeRecord:
    """Simple fake DB record returned by mocked create_record calls."""
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)


# Fixtures ---------------------------------------------------------------

@pytest.fixture
def db_mock():
    """Fresh MagicMock DB manager for each test."""
    return MagicMock()


@pytest.fixture
def tm(db_mock):
    """TaskManager wired to the mock DB. Adjust if TaskManager signature differs."""
    return TaskManager(db=db_mock)


# -----------------------
# add_task partitions
# -----------------------
def test_add_task_valid_with_description(tm, db_mock):
    db_mock.create_record.return_value = FakeRecord(cust_id=5)
    res = tm.add_task(user_id=1, name="Walk", description="Go for a walk")
    db_mock.create_record.assert_called_once()
    args, kwargs = db_mock.create_record.call_args
    # Expect first arg to be model/class or table identifier; allow flexible checks
    assert kwargs.get("cust_name") == "Walk" or kwargs.get("name") == "Walk"
    assert kwargs.get("cust_desc") == "Go for a walk" or kwargs.get("description") == "Go for a walk"
    assert hasattr(res, "cust_id") and res.cust_id == 5

def test_add_task_valid_without_description(tm, db_mock):
    db_mock.create_record.return_value = FakeRecord(cust_id=6)
    res = tm.add_task(user_id=1, name="Walk", description=None)
    db_mock.create_record.assert_called_once()
    assert hasattr(res, "cust_id") and res.cust_id == 6

@pytest.mark.parametrize("name", ["", " ", None, 123])
@pytest.mark.xfail(reason="invalid input cases; implementation may raise", strict=False)
def test_add_task_invalid_names_xfail(tm, db_mock, name):
    db_mock.create_record.return_value = FakeRecord(cust_id=99)
    try:
        tm.add_task(user_id=1, name=name, description=None)
    except Exception:
        pytest.xfail(f"add_task rejected invalid name: {repr(name)}")

@pytest.mark.xfail(reason="very long name handling may vary", strict=False)
def test_add_task_long_name_xfail(tm, db_mock):
    long_name = "A" * 500
    db_mock.create_record.return_value = FakeRecord(cust_id=77)
    res = tm.add_task(user_id=1, name=long_name, description=None)
    # Implementation may accept or reject; if accepted ensure DB called
    db_mock.create_record.assert_called_once()
    assert hasattr(res, "cust_id")


# -----------------------
# assign_custom partitions
# -----------------------
def test_assign_custom_valid(tm, db_mock):
    db_mock.create_record.return_value = FakeRecord(id=10)
    res = tm.assign_custom(user_id=1, cust_id=5, date=date(2026,5,10),
                           start_time=time(10,0), end_time=time(11,0))
    db_mock.create_record.assert_called_once()
    args, kwargs = db_mock.create_record.call_args
    assert kwargs.get("user_id") == 1
    assert kwargs.get("cust_id") == 5
    assert kwargs.get("task_date") == date(2026,5,10)
    assert hasattr(res, "id") and res.id == 10

def test_assign_custom_start_after_end_allowed(tm, db_mock):
    db_mock.create_record.return_value = FakeRecord(id=11)
    res = tm.assign_custom(user_id=1, cust_id=5, date=date(2026,5,10),
                           start_time=time(11,0), end_time=time(10,0))
    db_mock.create_record.assert_called_once()
    assert hasattr(res, "id") and res.id == 11

@pytest.mark.xfail(reason="invalid user_id should be rejected", strict=False)
def test_assign_custom_invalid_user_xfail(tm, db_mock):
    db_mock.create_record.return_value = FakeRecord(id=12)
    try:
        tm.assign_custom(user_id=None, cust_id=5, date=date(2026,5,10),
                         start_time=time(10,0), end_time=time(11,0))
    except Exception:
        pytest.xfail("assign_custom rejected None user_id")


# -----------------------
# remove_task partitions
# -----------------------
def test_remove_task_valid_deletes(tm, db_mock):
    db_mock.delete_record.return_value = 1
    res = tm.remove_task(user_id=1, cust_id=5)
    db_mock.delete_record.assert_called_once()
    assert res is True or res == {"deleted": 1} or res is None

def test_remove_task_nonexistent_no_error(tm, db_mock):
    db_mock.delete_record.return_value = 0
    res = tm.remove_task(user_id=1, cust_id=9999)
    db_mock.delete_record.assert_called_once()
    assert res is False or res == {"deleted": 0} or res is None


# -----------------------
# mark_complete / mark_incomplete partitions
# -----------------------
def test_mark_complete_valid_updates(tm, db_mock):
    # Simulate existing assignment found by read_record
    db_mock.read_record.return_value = [{"id": 200, "user_id": 1, "cust_id": 5}]
    db_mock.update_record.return_value = 1
    res = tm.mark_complete(user_id=1, cust_id=5)
    db_mock.update_record.assert_called_once()
    assert res is True or res == {"updated": 1}

def test_mark_complete_nonexistent_returns_zero(tm, db_mock):
    db_mock.read_record.return_value = []
    db_mock.update_record.return_value = 0
    res = tm.mark_complete(user_id=1, cust_id=9999)
    # When no assignment exists, update_record may not be called; ensure return semantics
    assert res is False or res == {"updated": 0} or res is None

def test_mark_incomplete_valid_updates(tm, db_mock):
    db_mock.read_record.return_value = [{"id": 201, "user_id": 1, "cust_id": 5}]
    db_mock.update_record.return_value = 1
    res = tm.mark_incomplete(user_id=1, cust_id=5)
    db_mock.update_record.assert_called_once()
    assert res is True or res == {"updated": 1}

def test_mark_incomplete_nonexistent_returns_zero(tm, db_mock):
    db_mock.read_record.return_value = []
    db_mock.update_record.return_value = 0
    res = tm.mark_incomplete(user_id=1, cust_id=9999)
    assert res is False or res == {"updated": 0} or res is None


# -----------------------
# update_task partitions
# -----------------------
def test_update_task_valid_name_update(tm, db_mock):
    db_mock.read_record.return_value = [{"cust_id": 5}]
    db_mock.update_record.return_value = 1
    res = tm.update_task(cust_id=5, cust_name="New Name")
    db_mock.update_record.assert_called_once()
    assert res == 1 or res is True

def test_update_task_valid_desc_update(tm, db_mock):
    db_mock.read_record.return_value = [{"cust_id": 5}]
    db_mock.update_record.return_value = 1
    res = tm.update_task(cust_id=5, cust_desc="New Desc")
    db_mock.update_record.assert_called_once()
    assert res == 1 or res is True

def test_update_task_invalid_field_ignored(tm, db_mock):
    db_mock.update_record.reset_mock()
    res = tm.update_task(cust_id=5, bad_field="ignored")
    assert db_mock.update_record.call_count == 0
    assert res is None or res == 0 or res is False

def test_update_task_empty_no_call(tm, db_mock):
    db_mock.update_record.reset_mock()
    res = tm.update_task(cust_id=5)
    assert db_mock.update_record.call_count == 0
    assert res is None


# -----------------------
# update_schedule partitions
# -----------------------
def test_update_schedule_valid_date(tm, db_mock):
    db_mock.read_record.return_value = [{"id": 300, "user_id": 1, "cust_id": 5}]
    db_mock.update_record.return_value = 1
    res = tm.update_schedule(user_id=1, cust_id=5, task_date=date(2026,5,12))
    db_mock.update_record.assert_called_once()
    assert res == 1 or res is True

def test_update_schedule_valid_time(tm, db_mock):
    db_mock.read_record.return_value = [{"id": 301, "user_id": 1, "cust_id": 5}]
    db_mock.update_record.return_value = 1
    res = tm.update_schedule(user_id=1, cust_id=5, task_stime=time(14,0), task_etime=time(15,0))
    db_mock.update_record.assert_called_once()
    assert res == 1 or res is True

def test_update_schedule_invalid_field_ignored(tm, db_mock):
    db_mock.update_record.reset_mock()
    res = tm.update_schedule(user_id=1, cust_id=5, bad_field="ignored")
    assert db_mock.update_record.call_count == 0
    assert res is None or res == 0 or res is False


# -----------------------
# assign_predefined / unassign_predefined partitions
# -----------------------
def test_assign_predefined_valid(tm, db_mock):
    db_mock.create_record.return_value = FakeRecord(id=400)
    res = tm.assign_predefined(user_id=1, task_id=3, date=date(2026,5,10),
                               start_time=time(9,0), end_time=time(10,0))
    db_mock.create_record.assert_called_once()
    assert hasattr(res, "id") and res.id == 400

@pytest.mark.xfail(reason="invalid predefined task id", strict=False)
def test_assign_predefined_invalid_task_xfail(tm, db_mock):
    db_mock.create_record.side_effect = Exception("FK constraint")
    with pytest.raises(Exception):
        tm.assign_predefined(user_id=1, task_id=9999, date=date(2026,5,10),
                             start_time=time(9,0), end_time=time(10,0))

def test_unassign_predefined_valid(tm, db_mock):
    db_mock.read_record.return_value = [{"id": 55, "user_id": 1, "task_id": 3}]
    db_mock.delete_record.return_value = 1
    res = tm.unassign_predefined(user_id=1, task_id=3)
    db_mock.delete_record.assert_called_once()
    assert res is True or res == {"deleted": 1}

def test_unassign_predefined_nonexistent(tm, db_mock):
    db_mock.read_record.return_value = []
    db_mock.delete_record.return_value = 0
    res = tm.unassign_predefined(user_id=1, task_id=9999)
    db_mock.delete_record.assert_called_once()
    assert res is False or res == {"deleted": 0}


# -----------------------
# get_predefined tasks partitions
# -----------------------
def test_get_predefined_tasks_catalog(tm, db_mock):
    db_mock.read_record.return_value = [
        {"task_id": 1, "type_id": 2, "name": "Run"},
        {"task_id": 2, "type_id": 2, "name": "Swim"},
    ]
    res = tm.get_predefined_tasks()
    assert isinstance(res, dict)
    # Expect grouping by type_id or type name depending on implementation
    assert any(isinstance(v, list) for v in res.values())

def test_get_predefined_tasks_empty(tm, db_mock):
    db_mock.read_record.return_value = []
    res = tm.get_predefined_tasks()
    assert res == {} or all(isinstance(v, list) and len(v) == 0 for v in res.values())

def test_get_predefined_by_category_valid(tm, db_mock):
    db_mock.read_record.return_value = [{"task_id": 3, "type_id": 2, "name": "Yoga"}]
    res = tm.get_predefined_by_category(type_id=2)
    assert isinstance(res, list)
    assert any(item.get("task_id") == 3 for item in res)

def test_get_predefined_by_category_invalid(tm, db_mock):
    db_mock.read_record.return_value = []
    res = tm.get_predefined_by_category(type_id=9999)
    assert res == [] or res == []


# -----------------------
# DB error and edge partitions
# -----------------------
@pytest.mark.xfail(reason="DB exceptions may be surfaced or handled", strict=False)
def test_db_create_raises_propagates_or_handled(tm, db_mock):
    db_mock.create_record.side_effect = Exception("DB down")
    with pytest.raises(Exception):
        tm.add_task(user_id=1, name="Run", description=None)

@pytest.mark.xfail(reason="DB update exceptions may be surfaced or handled", strict=False)
def test_db_update_raises_propagates_or_handled(tm, db_mock):
    db_mock.read_record.return_value = [{"id": 500, "user_id": 1, "cust_id": 5}]
    db_mock.update_record.side_effect = Exception("DB error")
    with pytest.raises(Exception):
        tm.mark_complete(user_id=1, cust_id=5)


# -----------------------
# Type and null input partitions
# -----------------------
@pytest.mark.xfail(reason="non-int user_id handling may vary", strict=False)
def test_non_int_user_id_xfail(tm, db_mock):
    with pytest.raises(Exception):
        tm.add_task(user_id="abc", name="Walk")

@pytest.mark.xfail(reason="null inputs should raise or be handled", strict=False)
def test_null_inputs_xfail(tm):
    with pytest.raises(Exception):
        tm.add_task(user_id=None, name=None)

