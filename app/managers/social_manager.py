from peewee import *


class SocialManager:
    """Manages friend requests, friendships, and social interactions between users."""

    def __init__(self, db):
        """Initializes the SocialManager.

        Args:
            db: The database manager instance containing Peewee models.
        """
        self._db = db
        self.friends_table = self._db.models["Friends"]
        self.user_table = self._db.models["Users"].alias()

    def add_friend(self, user_id, friend_id):
        """Sends a friend request from one user to another.

        Args:
            user_id (int): ID of the user sending the request.
            friend_id (int): ID of the user receiving the request.

        Returns:
            dict | bool: Error message dict if invalid, otherwise True.
        """
        if user_id == friend_id:
            return {"error": "You cannot friend yourself"}

        existing = self.friends_table.get_or_none(
            (self.friends_table.user_id == user_id) &
            (self.friends_table.friend_id == friend_id)
        )

        if existing:
            return {"error": "Friend request already exists or you are already friends"}

        # Create mirrored friend request entries
        self.friends_table.create(
            user_id=user_id,
            friend_id=friend_id,
            friend_status="Pending - Sent"
        )
        self.friends_table.create(
            user_id=friend_id,
            friend_id=user_id,
            friend_status="Pending - Received"
        )

        return True

    def remove_friend(self, user_id, friend_id):
        """Removes a friendship or cancels a friend request.

        Args:
            user_id (int): First user ID.
            friend_id (int): Second user ID.

        Returns:
            dict: Success or error message.
        """
        deleted = self.friends_table.delete().where(
            ((self.friends_table.user_id == user_id) & (self.friends_table.friend_id == friend_id)) |
            ((self.friends_table.user_id == friend_id) & (self.friends_table.friend_id == user_id))
        ).execute()

        if deleted == 0:
            return {"error": "No friendship or request found"}

        return {"success": True, "message": "Friendship removed"}

    def view_friends(self, user_id):
        """Retrieves a list of friends or pending requests for a user.

        Args:
            user_id (int): User ID whose friends should be retrieved.

        Returns:
            list[dict]: List of friends with:
                - friend_id (int)
                - username (str)
                - status (str)
        """
        friends = (
            self.user_table
            .select(
                self.user_table.user_id,
                self.user_table.username,
                self.friends_table.friend_status
            )
            .join(self.friends_table, on=(self.friends_table.friend_id == self.user_table.user_id))
            .where(
                (self.friends_table.user_id == user_id) &
                (
                    (self.friends_table.friend_status == "Friends") |
                    (self.friends_table.friend_status == "Pending - Sent")
                )
            )
        )

        return [
            {
                "friend_id": f.user_id,
                "username": f.username,
                "status": f.friend_id.friend_status
            }
            for f in friends
        ]

    def view_friend_status(self, user_id, friend_id):
        """Checks the friendship status between two users.

        Args:
            user_id (int): First user ID.
            friend_id (int): Second user ID.

        Returns:
            dict: Status message such as:
                - "Not Friends"
                - "Pending - Sent"
                - "Pending - Received"
                - "Friends"
        """
        record = self.friends_table.get_or_none(
            (self.friends_table.user_id == user_id) &
            (self.friends_table.friend_id == friend_id)
        )

        if not record:
            return {"status": "Not Friends"}

        return {"status": record.friend_status}