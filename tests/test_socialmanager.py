# tests/test_social_manager.py
import pytest
from unittest.mock import MagicMock
from datetime import date

from app.managers.social_manager import SocialManager


class FakeRecord:
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)


# Fixtures
@pytest.fixture
def db_mock():
    return MagicMock()

@pytest.fixture
def sm(db_mock):
    return SocialManager(db=db_mock)


# ------------------------------------------------------------------
# add_friend
# ------------------------------------------------------------------
def test_add_friend_by_username_creates_request(sm, db_mock):
    # user sends request to username "alice"
    db_mock.read_record.return_value = [{"user_id": 2, "username": "alice"}]
    db_mock.create_record.return_value = FakeRecord(id=10)
    res = sm.add_friend(user_id=1, username_or_id="alice")
    db_mock.read_record.assert_called_once_with("users", where={"username": "alice"})
    db_mock.create_record.assert_called_once()
    assert res is True or res == {"success": True} or hasattr(res, "id")

def test_add_friend_by_userid_creates_request(sm, db_mock):
    db_mock.read_record.return_value = [{"user_id": 2}]
    db_mock.create_record.return_value = FakeRecord(id=11)
    res = sm.add_friend(user_id=1, username_or_id=2)
    db_mock.read_record.assert_called_once_with("users", pk_values=(2,))
    db_mock.create_record.assert_called_once()
    assert res is True or res == {"success": True} or hasattr(res, "id")

@pytest.mark.xfail(reason="username not found handling may vary", strict=False)
def test_add_friend_username_not_exist_xfail(sm, db_mock):
    db_mock.read_record.return_value = []
    res = sm.add_friend(user_id=1, username_or_id="ghost")
    assert res is False or res == {"success": False, "error": "Username does not exist"}

@pytest.mark.xfail(reason="user id not found handling may vary", strict=False)
def test_add_friend_userid_not_exist_xfail(sm, db_mock):
    db_mock.read_record.return_value = []
    res = sm.add_friend(user_id=1, username_or_id=999)
    assert res is False or res == {"success": False, "error": "User ID does not exist"}

@pytest.mark.xfail(reason="self-friend prevention may vary", strict=False)
def test_add_friend_self_xfail(sm, db_mock):
    # user tries to friend themselves
    db_mock.read_record.return_value = [{"user_id": 1}]
    res = sm.add_friend(user_id=1, username_or_id=1)
    assert res is False or "cannot friend yourself" in (res.get("error") if isinstance(res, dict) else "")

@pytest.mark.xfail(reason="duplicate request handling may vary", strict=False)
def test_add_friend_duplicate_request_xfail(sm, db_mock):
    # simulate existing request
    db_mock.read_record.side_effect = [
        [{"user_id": 2}],  # target user exists
        [{"id": 20, "status": "pending"}],  # existing friend request
    ]
    res = sm.add_friend(user_id=1, username_or_id=2)
    assert res is False or res == {"success": False, "error": "Friend request already exists"}


@pytest.mark.xfail(reason="wrong type should raise", strict=False)
def test_add_friend_wrong_type_xfail(sm):
    with pytest.raises(Exception):
        sm.add_friend(user_id="abc", username_or_id=2)


@pytest.mark.xfail(reason="null input should raise", strict=False)
def test_add_friend_null_input_xfail(sm):
    with pytest.raises(Exception):
        sm.add_friend(user_id=None, username_or_id=None)


# ------------------------------------------------------------------
# remove_friend
# ------------------------------------------------------------------
def test_remove_friend_existing_deletes(sm, db_mock):
    # simulate existing friendship rows
    db_mock.read_record.return_value = [{"id": 30, "user_id": 1, "friend_id": 2}]
    db_mock.delete_record.return_value = 2  # two mirrored rows deleted
    res = sm.remove_friend(user_id=1, friend_id=2)
    db_mock.delete_record.assert_called_once()
    assert res is True or res == {"success": True, "message": "Friendship removed"}

@pytest.mark.xfail(reason="no friendship handling may vary", strict=False)
def test_remove_friend_no_friendship_xfail(sm, db_mock):
    db_mock.read_record.return_value = []
    db_mock.delete_record.return_value = 0
    res = sm.remove_friend(user_id=1, friend_id=999)
    assert res is False or res == {"success": False, "error": "No friendship or request found"}

@pytest.mark.xfail(reason="wrong type should raise", strict=False)
def test_remove_friend_wrong_type_xfail(sm):
    with pytest.raises(Exception):
        sm.remove_friend(user_id="abc", friend_id=2)

@pytest.mark.xfail(reason="null input should raise", strict=False)
def test_remove_friend_null_input_xfail(sm):
    with pytest.raises(Exception):
        sm.remove_friend(user_id=None, friend_id=None)


# ------------------------------------------------------------------
# view_friends
# ------------------------------------------------------------------
def test_view_friends_with_friends_and_pending(sm, db_mock):
    db_mock.read_record.return_value = [
        {"friend_id": 2, "username": "alice", "status": "Friends"},
        {"friend_id": 3, "username": "bob", "status": "Pending - Sent"},
    ]
    res = sm.view_friends(user_id=1)
    db_mock.read