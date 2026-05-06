from peewee import *
from app.db.database_models import *
from datetime import date


class NotificationManager:
    """Handles retrieval of notifications such as friend requests,
    competition invites, and competition deadlines.
    """

    def __init__(self):
        """Initializes the NotificationManager."""
        pass

    def get_friend_requests(self, user_id):
        """Fetches all pending friend requests for a user.

        Args:
            user_id (int): The ID of the user receiving friend requests.

        Returns:
            list[dict]: A list of dictionaries containing:
                - from_user (int): ID of the user who sent the request.
                - status (str): Current status of the friend request.
        """
        requests = self.friends_table.select().where(
            (self.friends_table.user_id == user_id) &
            (self.friends_table.friend_status == "Pending - Received")
        )

        return [
            {
                "from_user": req.friend_id,
                "status": req.friend_status
            }
            for req in requests
        ]

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
        invites = CompParticipant.select().where(
            (CompParticipant.user_id == user_id) &
            (CompParticipant.comp_status == "Pending")
        )

        return [
            {
                "competition_id": inv.comp_id.id,
                "competition_name": inv.comp_id.comp_name,
                "status": inv.comp_status
            }
            for inv in invites
        ]

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
            Competitions
            .select()
            .join(CompParticipant, on=(Competitions.comp_id == CompParticipant.comp_id))
            .where(
                (CompParticipant.user_id == user_id) &
                (Competitions.comp_edate >= today)
            )
        )

        return [
            {
                "competition_id": comp.comp_id,
                "competition_name": comp.comp_name,
                "end_date": comp.comp_edate,
                "days_left": (comp.comp_edate - today).days
            }
            for comp in deadlines
        ]


def test():
    nm = NotificationManager()
    print(nm.get_friend_requests(2))
    # print(nm.get_competition_invites(1))
    # print(nm.get_competition_deadlines(1))


test()