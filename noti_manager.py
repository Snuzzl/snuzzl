import asyncio
from concurrent.futures import ThreadPoolExecutor
from peewee import *
from database_models import *
from datetime import date

class NotificationManager:

    def __init__(self):
        pass

    def get_friend_requests(self, user_id):
        requests = Friends.select().where(
            (Friends.user_id == user_id) &
            (Friends.friend_status == "Pending - Received")
        )

        return [
            {
                "from_user": req.friend_id.id,
                "status": req.friend_status
            }
            for req in requests
        ]

    def get_competition_invites(self, user_id):
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
        today = date.today()

        # Join competitions through compParticipant
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