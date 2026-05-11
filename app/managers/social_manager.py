class SocialManager:
    """Manages friendship relationships and social interactions between users."""

    def __init__(self, db):
        """Initialize the SocialManager with database models.

        Args:
            db: Database manager instance containing models and CRUD methods.
        """

        self._db = db
        self.friends_table = self._db.models["Friends"]
        self.users_table = self._db.models["Users"]

    def add_friend(self, user_id, username_or_id):
        """Send a friend request to another user.

        Accepts either a username or user ID to identify the
        recipient of the friend request.

        Args:
            user_id (int): The ID of the user sending the request.
            username_or_id (str | int): Username or user ID of the target user.

        Returns:
            dict: Result of the operation containing success status and
                optional error information.
        """
        # Check between username or id
        id_check = None
        try:
            id_check = int(username_or_id)
        except Exception:
            try:
                user = self.users_table.get(self.users_table.username == username_or_id)
                friend_id = user.user_id
            except Exception:
                return {"success": False, "error": "Username does not exist"}
        if id_check:
            try:
                user = self.users_table.get(self.users_table.user_id == username_or_id)
                friend_id = user.user_id
            except Exception:
                return {"success": False, "error": "User ID does not exist"}

        # Check if friend_id is current user_id
        if user_id == friend_id:
            return {"success": False, "error": "You cannot friend yourself"}

        #Check if record already exists in friends table
        existing = self.friends_table.get_or_none((self.friends_table.user_id == user_id) & (self.friends_table.friend_id == friend_id))
        if existing:
            return {"success": False, "error": "Friend request already exists or you are already friends"}

        # Create mirrored friend request entries.
        self.friends_table.create(
            user_id=user_id,
            friend_id=friend_id,
            friend_status="Pending - Sent",
        )
        self.friends_table.create(
            user_id=friend_id,
            friend_id=user_id,
            friend_status="Pending - Received",
        )
        return {"success": True}

    def remove_friend(self, user_id, friend_id):
        """Remove a friendship or pending friend request.

        Deletes both mirrored friendship records between two users.

        Args:
            user_id (int): The ID of the requesting user.
            friend_id (int): The ID of the friend to remove.

        Returns:
            dict: Result of the operation containing success status and
                optional message or error information.
        """
        deleted = (
            self.friends_table.delete()
            .where(
                ((self.friends_table.user_id == user_id) & (self.friends_table.friend_id == friend_id)) | 
                ((self.friends_table.user_id == friend_id) & (self.friends_table.friend_id == user_id))
            ).execute()
        )

        if deleted == 0:
            return {"success": False, "error": "No friendship or request found",}

        return {"success": True, "message": "Friendship removed"}

    def view_friends(self, user_id):
        """Retrieve a user's friends and outgoing pending requests.

        Args:
            user_id (int): The ID of the user whose friends are being queried.

        Returns:
            list[dict]: List of friend records containing friend ID,
                username, and friendship status.
        """
        friends = (
            self.users_table
            .select(
                self.users_table.user_id,
                self.users_table.username,
                self.friends_table.friend_status,
            )
            .join(self.friends_table, on=(self.friends_table.friend_id == self.users_table.user_id),)
            .where(
                (self.friends_table.user_id == user_id) & 
                ((self.friends_table.friend_status == "Friends") | ( self.friends_table.friend_status== "Pending - Sent"))
            )
        )

        return [
            {
                "friend_id": f.user_id,
                "username": f.username,
                "status": f.friend_id.friend_status,
            }
            for f in friends
        ]

    def view_friend_status(self, user_id, friend_id):
        """Get the friendship status between two users.

        Args:
            user_id (int): The ID of the user making the query.
            friend_id (int): The ID of the other user.

        Returns:
            dict: Dictionary containing the friendship status.
        """
        record = self.friends_table.get_or_none((self.friends_table.user_id == user_id) & (self.friends_table.friend_id == friend_id))
        if not record:
            return {"status": "Not Friends"}

        return {"status": record.friend_status}