import asyncio
from concurrent.futures import ThreadPoolExecutor
from peewee import *
from database_models import *

class SocialManager:

    def __init__(self, db):
        self.db = db

    def add_friend(self, user_id, friend_id):
        # Prevent self-friend
        if user_id == friend_id:
            return {"error": "You cannot friend yourself"}

        # Check if already exists
        existing = Friends.get_or_none(
            (Friends.user_id == user_id) & (Friends.friend_id == friend_id)
        )

        if existing:
            return {"error": "Friend request already exists or you are already friends"}

        # Create two entries: sent + received
        Friends.create(
            user_id=user_id,
            friend_id=friend_id,
            friend_status="Pending - Sent"
        )
        Friends.create(
            user_id=friend_id,
            friend_id=user_id,
            friend_status="Pending - Received"
        )

        return {"success": True, "message": "Friend request sent"}

    def remove_friend(self, user_id, friend_id):
        deleted = Friends.delete().where(
            ((Friends.user_id == user_id) & (Friends.friend_id == friend_id)) |
            ((Friends.user_id == friend_id) & (Friends.friend_id == user_id))
        ).execute()

        if deleted == 0:
            return {"error": "No friendship or request found"}

        return {"success": True, "message": "Friendship removed"}

    def view_friends(self, user_id):
        friends = Friends.select().where(
            (Friends.user_id == user_id) &
            (Friends.friend_status == "Friends")
        )

        return [{"friend_id": f.friend_id.id, "status": f.friend_status} for f in friends]

    def view_friend_status(self, user_id, friend_id):
        record = Friends.get_or_none(
            (Friends.user_id == user_id) & (Friends.friend_id == friend_id)
        )

        if not record:
            return {"status": "Not Friends"}

        return {"status": record.friend_status}