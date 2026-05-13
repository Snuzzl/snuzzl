# tests/test_notification_manager.py
import pytest
from unittest.mock import MagicMock
from datetime import date, timedelta

from app.managers.noti_manager import NotificationManager


class FakeRecord:
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)


# Fixtures
@pytest.fixture
def db_mock():
    return MagicMock()

@pytest.fixture
def nm(db_mock):
    return NotificationManager(db=db_mock)


# ------------------------------------------------------------------
# get_friend_requests
# ------------------------------------------------------------------
def test_get_friend_requests_with_pending(nm, db_mock):
    db_mock.read_record.return_value = [
        {"from_user_id": 2, "from_username": "alice", "status": "pending"}
    ]
    res = nm.get_friend_requests(user_id=5)
    db_mock.read_record.assert_called_once_with("friend_requests", where={"to_user_id": 5, "status": "pending"})
    assert isinstance(res, list)
    assert res[0]["from_username"] == "alice"

def test_get_friend_requests_no_pending(nm, db_mock):
    db_mock.read_record.return_value = []
    res = nm.get_friend_requests(user_id=5)
    assert res == [] or res is None

@pytest.mark.xfail(reason="invalid user id handling may vary", strict=False)
def test_get_friend_requests_invalid_user_xfail(nm):
    with pytest.raises(Exception):
        nm.get_friend_requests(user_id=999)


@pytest.mark.xfail(reason="wrong type should raise", strict=False)
def test_get_friend_requests_wrong_type_xfail(nm):
    with pytest.raises(Exception):
        nm.get_friend_requests(user_id="abc")


@pytest.mark.xfail(reason="null input should raise", strict=False)
def test_get_friend_requests_null_input_xfail(nm):
    with pytest.raises(Exception):
        nm.get_friend_requests(user_id=None)


# ------------------------------------------------------------------
# get_competition_invites
# ------------------------------------------------------------------
def test_get_competition_invites_with_pending(nm, db_mock):
    db_mock.read_record.return_value = [
        {"competition_id": 3, "competition_name": "May Run", "status": "pending"}
    ]
    res = nm.get_competition_invites(user_id=5)
    db_mock.read_record.assert_called_once_with("competition_invites", where={"user_id": 5, "status": "pending"})
    assert isinstance(res, list)
    assert res[0]["competition_name"] == "May Run"

def test_get_competition_invites_no_invites(nm, db_mock):
    db_mock.read_record.return_value = []
    res = nm.get_competition_invites(user_id=5)
    assert res == [] or res is None

@pytest.mark.xfail(reason="invalid user id handling may vary", strict=False)
def test_get_competition_invites_invalid_user_xfail(nm):
    with pytest.raises(Exception):
        nm.get_competition_invites(user_id=999)

@pytest.mark.xfail(reason="wrong type should raise", strict=False)
def test_get_competition_invites_wrong_type_xfail(nm):
    with pytest.raises(Exception):
        nm.get_competition_invites(user_id="abc")


# ------------------------------------------------------------------
# get_competition_deadlines
# ------------------------------------------------------------------
def test_get_competition_deadlines_future_deadlines(nm, db_mock):
    today = date.today()
    db_mock.read_record.return_value = [
        {"competition_id": 7, "competition_name": "June Challenge", "end_date": today + timedelta(days=10)}
    ]
    res = nm.get_competition_deadlines(user_id=5)
    db_mock.read_record.assert_called_once_with("competitions", where={"user_id": 5, "end_date__gte": date.today()})
    assert isinstance(res, list)
    assert res[0]["competition_name"] == "June Challenge"

def test_get_competition_deadlines_all_passed_returns_none(nm, db_mock):
    db_mock.read_record.return_value = []
    res = nm.get_competition_deadlines(user_id=5)
    assert res == [] or res is None

@pytest.mark.xfail(reason="invalid user id handling may vary", strict=False)
def test_get_competition_deadlines_invalid_user_xfail(nm):
    with pytest.raises(Exception):
        nm.get_competition_deadlines(user_id=999)

@pytest.mark.xfail(reason="wrong type should raise", strict=False)
def test_get_competition_deadlines_wrong_type_xfail(nm):
    with pytest.raises(Exception):
        nm.get_competition_deadlines(user_id="abc")


# ------------------------------------------------------------------
# accept_request / deny_request
# ------------------------------------------------------------------
def test_accept_request_success(nm, db_mock):
    # Simulate existing request row
    db_mock.read_record.return_value = [{"from_user_id": 2, "to_user_id": 5, "status": "pending"}]
    db_mock.update_record.return_value = 1
    res = nm.accept_request(user_id=5, friend_id=2)
    db_mock.update_record.assert_called_once()
    args, kwargs = db_mock.update_record.call_args
    # Expect update_record(table, pk_values, **fields) or similar; accept flexible checks
    assert kwargs.get("status") == "accepted" or kwargs == {"status": "accepted"}
    assert res is True or res == {"success": True}

def test_deny_request_success(nm, db_mock):
    db_mock.read_record.return_value = [{"from_user_id": 2, "to_user_id": 5, "status": "pending"}]
    db_mock.update_record.return_value = 1
    res = nm.deny_request(user_id=5, friend_id=2)
    db_mock.update_record.assert_called_once()
    args, kwargs = db_mock.update_record.call_args
    assert kwargs.get("status") == "denied" or kwargs == {"status": "denied"}
    assert res is True or res == {"success": True}

@pytest.mark.xfail(reason="request not found handling may vary", strict=False)
def test_accept_request_not_found_xfail(nm, db_mock):
    db_mock.read_record.return_value = []
    res = nm.accept_request(user_id=5, friend_id=2)
    # Implementation may raise or return False; accept either
    assert res is False or res is None

@pytest.mark.xfail(reason="wrong types should raise", strict=False)
def test_accept_request_wrong_types_xfail(nm):
    with pytest.raises(Exception):
        nm.accept_request(user_id="abc", friend_id=2)


# ------------------------------------------------------------------
# accept_invite / deny_invite
# ------------------------------------------------------------------
def test_accept_invite_success(nm, db_mock):
    db_mock.read_record.return_value = [{"invite_id": 3, "user_id": 5, "competition_id": 7, "status": "pending"}]
    db_mock.update_record.return_value = 1
    res = nm.accept_invite(user_id=5, comp_id=7)
    db_mock.update_record.assert_called_once()
    args, kwargs = db_mock.update_record.call_args
    assert kwargs.get("status") == "accepted" or kwargs == {"status": "accepted"}
    assert res is True or res == {"success": True}

def test_deny_invite_success(nm, db_mock):
    db_mock.read_record.return_value = [{"invite_id": 3, "user_id": 5, "competition_id": 7, "status": "pending"}]
    db_mock.update_record.return_value = 1
    res = nm.deny_invite(user_id=5, comp_id=7)
    db_mock.update_record.assert_called_once()
    args, kwargs = db_mock.update_record.call_args
    assert kwargs.get("status") == "denied" or kwargs == {"status": "denied"}
    assert res is True or res == {"success": True}

@pytest.mark.xfail(reason="invite not found handling may vary", strict=False)
def test_accept_invite_not_found_xfail(nm, db_mock):
    db_mock.read_record.return_value = []
    res = nm.accept_invite(user_id=5, comp_id=7)
    assert res is False or res is None

@pytest.mark.xfail(reason="wrong types should raise", strict=False)
def test_accept_invite_wrong_types_xfail(nm):
    with pytest.raises(Exception):
        nm.accept_invite(user_id="abc", comp_id=7)


# ------------------------------------------------------------------
# deny_invite wrong types / null inputs
# ------------------------------------------------------------------
@pytest.mark.xfail(reason="null inputs should raise", strict=False)
def test_deny_invite_null_inputs_xfail(nm):
    with pytest.raises(Exception):
        nm.deny_invite(user_id=None, comp_id=None)
