"""Tests for TaskManager.

These tests mock the DatabaseManager to avoid hitting the real PostgreSQL
database. They verify that TaskManager calls the right DB methods with the
correct arguments and handles edge cases properly.
"""

import pytest
from unittest.mock import MagicMock, patch
from datetime import date, time

from app.managers.task_manager import TaskManager


class FakeRecord:
    """Simple fake database record for mocking create_record returns."""

    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)


@pytest.fixture
def db_mock():
    """Fresh MagicMock database manager for each test."""
    return MagicMock()


@pytest.fixture
def tm(db_mock):
    """TaskManager instance wired to the mock DB."""
    return TaskManager(db=db_mock)


# ------------------------------------------------------------------
# add_task
# ------------------------------------------------------------------


def test_add_task_success(tm, db_mock):
    db_mock.create_record.return_value = FakeRecord(cust_id=1, cust_name="Walk")

    result = tm.add_task(None, "Walk", "Go for a walk")

    db_mock.create_record.assert_called_once()
    args, kwargs = db_mock.create_record.call_args
    assert args[0].__name__ == "CustomTasks"
    assert kwargs["cust_name"] == "Walk"
    assert kwargs["cust_desc"] == "Go for a walk"
    assert result.cust_id == 1


def test_add_task_empty_name_raises(tm):
    with pytest.raises(ValueError, match="cannot be empty"):
        tm.add_task(None, "")


def test_add_task_whitespace_name_raises(tm):
    with pytest.raises(ValueError, match="cannot be empty"):
        tm.add_task(None, "   ")


# ------------------------------------------------------------------
# assign_custom
# ------------------------------------------------------------------


def test_assign_custom(tm, db_mock):
    d = date(2026, 5, 10)
    st = time(10, 0)
    et = time(11, 0)

    tm.assign_custom(1, 5, d, st, et)

    db_mock.create_record.assert_called_once()
    args, kwargs = db_mock.create_record.call_args
    assert args[0].__name__ == "UserTask"
    assert kwargs["user_id"] == 1
    assert kwargs["task_id"] is None
    assert kwargs["cust_id"] == 5
    assert kwargs["task_complete"] is False
    assert kwargs["task_date"] == d
    assert kwargs["task_stime"] == st
    assert kwargs["task_etime"] == et


# ------------------------------------------------------------------
# remove_task
# ------------------------------------------------------------------


def test_remove_task(tm, db_mock):
    tm.remove_task(1, 5)

    calls = db_mock.delete_record.call_args_list
    assert len(calls) == 2
    # First call removes UserTask assignment
    assert calls[0][0][0].__name__ == "UserTask"
    assert calls[0][0][1] == (1, 5)
    # Second call removes CustomTasks record
    assert calls[1][0][0].__name__ == "CustomTasks"
    assert calls[1][0][1] == 5


# ------------------------------------------------------------------
# mark_complete / mark_incomplete
# ------------------------------------------------------------------


def test_mark_complete(tm, db_mock):
    tm.mark_complete(1, 5)
    db_mock.update_record.assert_called_once()
    args, kwargs = db_mock.update_record.call_args
    assert args[1] == (1, 5)
    assert kwargs == {"task_complete": True}


def test_mark_incomplete(tm, db_mock):
    tm.mark_incomplete(1, 5)
    db_mock.update_record.assert_called_once()
    args, kwargs = db_mock.update_record.call_args
    assert args[1] == (1, 5)
    assert kwargs == {"task_complete": False}


# ------------------------------------------------------------------
# update_task
# ------------------------------------------------------------------


def test_update_task_name_and_desc(tm, db_mock):
    tm.update_task(5, cust_name="New name", cust_desc="New desc")
    db_mock.update_record.assert_called_once()
    args, kwargs = db_mock.update_record.call_args
    assert args[1] == 5
    assert kwargs == {"cust_name": "New name", "cust_desc": "New desc"}


def test_update_task_ignores_invalid_fields(tm, db_mock):
    tm.update_task(5, cust_name="Valid", bad_field="ignored")
    db_mock.update_record.assert_called_once()
    args, kwargs = db_mock.update_record.call_args
    assert args[1] == 5
    assert kwargs == {"cust_name": "Valid"}


def test_update_task_no_valid_fields_no_call(tm, db_mock):
    tm.update_task(5, bad_field="ignored")
    db_mock.update_record.assert_not_called()


# ------------------------------------------------------------------
# update_schedule
# ------------------------------------------------------------------


def test_update_schedule(tm, db_mock):
    d = date(2026, 5, 12)
    st = time(14, 0)
    et = time(15, 0)

    tm.update_schedule(1, 5, task_date=d, task_stime=st, task_etime=et)

    db_mock.update_record.assert_called_once()
    args, kwargs = db_mock.update_record.call_args
    assert args[1] == (1, 5)
    assert kwargs == {"task_date": d, "task_stime": st, "task_etime": et}


def test_update_schedule_ignores_invalid_fields(tm, db_mock):
    d = date(2026, 5, 12)
    tm.update_schedule(1, 5, task_date=d, bad_field="ignored")
    db_mock.update_record.assert_called_once()
    args, kwargs = db_mock.update_record.call_args
    assert args[1] == (1, 5)
    assert kwargs == {"task_date": d}


# ------------------------------------------------------------------
# assign_predefined / unassign_predefined
# ------------------------------------------------------------------


def test_assign_predefined(tm, db_mock):
    d = date(2026, 5, 10)
    st = time(9, 0)
    et = time(10, 0)

    tm.assign_predefined(1, 3, d, st, et)

    db_mock.create_record.assert_called_once()
    args, kwargs = db_mock.create_record.call_args
    assert args[0].__name__ == "UserTask"
    assert kwargs["user_id"] == 1
    assert kwargs["task_id"] == 3
    assert kwargs["cust_id"] is None
    assert kwargs["task_complete"] is False


def test_unassign_predefined(tm, db_mock):
    tm.unassign_predefined(1, 3)
    db_mock.delete_record.assert_called_once()
    args, kwargs = db_mock.delete_record.call_args
    assert args[1] == (1, 3)


# ------------------------------------------------------------------
# get_predefined_tasks / get_predefined_by_category
# ------------------------------------------------------------------


def test_get_predefined_tasks_queries_and_groups(tm):
    fake_task = MagicMock()
    fake_task.task_id = 1
    fake_task.task_name = "Run"
    fake_task.task_desc = "Go running"
    fake_task.type_id.type_id = 2
    fake_task.type_id.type_name = "Exercise"

    mock_query = MagicMock()
    mock_query.order_by.return_value = [fake_task]
    mock_join1 = MagicMock()
    mock_join1.join.return_value = mock_query

    with patch("app.managers.task_manager.Tasks") as MockTasks:
        MockTasks.select.return_value = mock_join1
        result = tm.get_predefined_tasks()

    assert "Exercise" in result
    assert len(result["Exercise"]) == 1
    assert result["Exercise"][0]["task_name"] == "Run"


def test_get_predefined_by_category_filters(tm):
    fake_task = MagicMock()
    fake_task.task_id = 1
    fake_task.task_name = "Run"
    fake_task.task_desc = "Go running"
    fake_task.type_id.type_id = 2
    fake_task.type_id.type_name = "Exercise"

    with patch("app.managers.task_manager.Tasks") as MockTasks:
        MockTasks.select.return_value.join.return_value.where.return_value.order_by.return_value = [fake_task]
        result = tm.get_predefined_by_category(2)

    assert len(result) == 1
    assert result[0]["task_name"] == "Run"
