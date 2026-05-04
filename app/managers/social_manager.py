from peewee import *

class SocialManager:

    def __init__(self, db):
        self._db = db
        self.friends_table = self._db.models["Friends"]
        self.user_table = self._db.models["Users"].alias()

    def add_friend(self, user_id, friend_id):
        if user_id == friend_id:
            return {"error": "You cannot friend yourself"}

        existing = self.friends_table.get_or_none(
            (self.friends_table.user_id == user_id) & (self.friends_table.friend_id == friend_id)
        )

        if existing:
            return {"error": "Friend request already exists or you are already friends"}

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
        deleted = self.friends_table.delete().where(
            ((self.friends_table.user_id == user_id) & (self.friends_table.friend_id == friend_id)) |
            ((self.friends_table.user_id == friend_id) & (self.friends_table.friend_id == user_id))
        ).execute()

        if deleted == 0:
            return {"error": "No friendship or request found"}

        return {"success": True, "message": "Friendship removed"}


    # Query returns a friend list for a given user
    def view_friends(self, user_id):
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
                    (self.friends_table.friend_status == "Friends" ) |
                    (self.friends_table.friend_status == "Pending - Sent" )
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
        record = self.friends_table.get_or_none(
            (self.friends_table.user_id == user_id) & (self.friends_table.friend_id == friend_id)
        )

        if not record:
            return {"status": "Not Friends"}

        return {"status": record.friend_status}
    
# db = DatabaseManager()  
# sm = SocialManager(db)
