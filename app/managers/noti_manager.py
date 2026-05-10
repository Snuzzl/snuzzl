from datetime import date


class NotificationManager:
    def __init__(self, db):
        """Handles retrieval of notifications such as friend requests,
        competition invites, and competition deadlines.
        """
        # database manager import
        self._db = db
        # Database tables
        self.friends_table = self._db.models["Friends"]
        self.users_table = self._db.models["Users"]
        self.competitions_table = self._db.models["Competitions"]
        self.comp_participant_table = self._db.models["CompParticipant"]

    def get_friend_requests(self, user_id):
        """Fetches all pending friend requests for a user.

        Args:
            user_id (int): The ID of the user receiving friend requests.

        Returns:
            list[dict]: A list of dictionaries containing:
                - from_user_id (int): ID of the user who sent the request.
                - from_username (int): Username of the user who sent the request.
                - status (str): Current status of the friend request.
        """
        requests = (
            self.friends_table.select(
                self.friends_table.friend_status,
                self.users_table.username,
                self.users_table.user_id
            )
            .join(self.users_table, on=(self.friends_table.friend_id == self.users_table.user_id))
            .where(
            (self.friends_table.user_id == user_id) &
            (self.friends_table.friend_status == "Pending - Received")
            )
        )
        if requests:
            return [
                {
                    "from_user_id": req.friend_id.user_id,
                    "from_username": req.friend_id.username,
                    "status": req.friend_status
                }
                for req in requests
            ]
        else:
            return None

    def get_competition_invites(self, user_id):
        """Fetches all pending competition invitations for a user.

        Args:
            user_id (int): The ID of the user receiving competition invites.

        Returns:
            list[dict]: A list of dictionaries containing:
                - competition_id (int): ID of the competition.
                - competition_name (str): Name of the competition.
                - status (str): Invitation status.
        """
        invites = (
            self.comp_participant_table.select(
                self.competitions_table.comp_id,
                self.competitions_table.comp_name,
                self.comp_participant_table.comp_status
            )
            .join(self.competitions_table, on=(self.comp_participant_table.comp_id == self.competitions_table.comp_id))
            .where(
                (self.comp_participant_table.user_id == user_id) &
                (self.comp_participant_table.comp_status == "Pending")
            )
        )
        if invites:
            return [
                {
                    "competition_id": inv.comp_id.comp_id,
                    "competition_name": inv.comp_id.comp_name,
                    "status": inv.comp_status
                }
                for inv in invites
            ]
        else:
            return None

    def get_competition_deadlines(self, user_id):
        """Fetches upcoming competition deadlines for a user.

        Args:
            user_id (int): The ID of the user participating in competitions.

        Returns:
            list[dict]: A list of dictionaries containing:
                - competition_id (int): ID of the competition.
                - competition_name (str): Name of the competition.
                - end_date (date): Competition end date.
                - days_left (int): Days remaining until the deadline.
        """
        today = date.today()
        deadlines = (
            self.competitions_table
            .select()
            .join(self.comp_participant_table, on=(self.competitions_table.comp_id == self.comp_participant_table.comp_id))
            .where(
                (self.comp_participant_table.user_id == user_id) &
                (self.competitions_table.comp_edate >= today)
            )
        )
        if deadlines:
            return [
                {
                    "competition_id": comp.comp_id,
                    "competition_name": comp.comp_name,
                    "end_date": comp.comp_edate,
                    "days_left": (comp.comp_edate - today).days
                }
                for comp in deadlines
            ]
        else:
            return None
        
    def accept_request(self, user_id, friend_id):
        existing = self.friends_table.get_or_none((self.friends_table.user_id == user_id) & (self.friends_table.friend_id == friend_id))
        if existing:
            self._db.update_record(self.friends_table, (user_id, friend_id), friend_status="Friends")
            self._db.update_record(self.friends_table, (friend_id, user_id), friend_status="Friends")
            return {'success': True, 'message': "Friend request accepted"}
        return {'success': False, 'error': "Friend request doesn't exist"}

    def deny_request(self, user_id, friend_id):
        existing = self.friends_table.get_or_none((self.friends_table.user_id == user_id) & (self.friends_table.friend_id == friend_id))
        if existing:
            self._db.delete_record(self.friends_table, (user_id, friend_id))
            self._db.delete_record(self.friends_table, (friend_id, user_id))
            return {'success': True, 'message': "Friend request denied"}
        return {'success': False, 'error': "Friend request doesn't exist"}

    def accept_invite(self, user_id, comp_id):
        existing = self.comp_participant_table.get_or_none((self.comp_participant_table.user_id == user_id) & (self.comp_participant_table.comp_id == comp_id))
        if existing:
            self._db.update_record(self.comp_participant_table, (user_id, comp_id), comp_status="In Comp")
            return {'success': True, 'message': "Competition invite accepted"}
        return {'success': False, 'error': "Competition invite doesn't exist"}

    def deny_invite(self, user_id, comp_id):
        existing = self.comp_participant_table.get_or_none((self.comp_participant_table.user_id == user_id) & (self.comp_participant_table.comp_id == comp_id))
        if existing:
            self._db.delete_record(self.comp_participant_table, (user_id, comp_id))
            return {'success': True, 'message': "Competition invite denied"}
        return {'success': False, 'error': "Competition invite doesn't exist"}