class SocialManager:
    """Manage friendships, friend requests, and social interactions between users."""

    def __init__(self, db):
        """Initialize the social manager.

        Args:
            db: Database manager instance containing Peewee models.
        """
        self._db = db
        self.friends_table = self._db.models["Friends"]
        self.users_table = self._db.models["Users"]

    def add_friend(self, user_id, username_or_id):
        """Send a friend request from one user to another.

        The target user can be identified either by username or by user ID.
        If the users are already connected or a request already exists,
        the request will not be created.

        Args:
            user_id (int): ID of the user sending the friend request.
            username_or_id (str | int): Username or user ID of the recipient.

        Returns:
            dict: Result dictionary containing:
                - success (bool): Whether the operation succeeded.
                - error (str, optional): Error message if the request failed.

        Examples:
            >>> manager.add_friend(1, "alice")
            {'success': True}

            >>> manager.add_friend(1, 2)
            {'success': True}
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

        # Check if freind_id is current user_id
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
        """Remove a friendship or cancel a friend request.

        This removes both relationship records between the two users.

        Args:
            user_id (int): ID of the first user.
            friend_id (int): ID of the second user.

        Returns:
            dict: Result dictionary containing:
                - success (bool): Whether the operation succeeded.
                - message (str, optional): Success message.
                - error (str, optional): Error message if no relationship exists.

        Examples:
            >>> manager.remove_friend(1, 2)
            {'success': True, 'message': 'Friendship removed'}
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
        """Retrieve a user's friends and pending outgoing requests.

        Args:
            user_id (int): ID of the user whose friend list should be retrieved.

        Returns:
            list[dict]: List of friend records. Each record contains:
                - friend_id (int): Friend's user ID.
                - username (str): Friend's username.
                - status (str): Friendship status.

        Examples:
            >>> manager.view_friends(1)
            [
                {
                    'friend_id': 2,
                    'username': 'alice',
                    'status': 'Friends'
                }
            ]
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
        """Retrieve the friendship status between two users.

        Args:
            user_id (int): ID of the first user.
            friend_id (int): ID of the second user.

        Returns:
            dict: Dictionary containing the friendship status.

                Possible status values:
                - "Not Friends"
                - "Pending - Sent"
                - "Pending - Received"
                - "Friends"

        Examples:
            >>> manager.view_friend_status(1, 2)
            {'status': 'Friends'}
        """
        record = self.friends_table.get_or_none((self.friends_table.user_id == user_id) & (self.friends_table.friend_id == friend_id))
        if not record:
            return {"status": "Not Friends"}

        return {"status": record.friend_status}