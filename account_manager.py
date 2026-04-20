import asyncio
from datetime import *
import hashlib
from database_manager import DatabaseManager
from database_models import Users
import time

dbm = DatabaseManager()

class AccountManager:
    def __init__(self,email,username,fname,dob,password):
        self.username = username
        self.email = email
        self.fname = fname
        self.dob = dob
        self.password = password

    async def _validateUsername(self, username):
        if not username or len(username) < 3:
            raise ValueError("Username must be at least 3 characters long")
        if not username.isalnum():
            raise ValueError("Username can only contain letters and numbers")
        return username

    def _validateEmail(self, email):
        if "@" not in email or "." not in email.split("@")[1]:
            raise ValueError("Invalid email format")
        return email

    def _validatePassword(self, password):
        if not password or len(password) < 6:
            raise ValueError("Password must be at least 6 characters long")
        return password

    async def createAccount(self):
        try:
            validate_username = await self._validateUsername(self.username)
            validate_email = self._validateEmail(self.email)
            validate_password = self._validatePassword(self.password)
            validate = True
        except ValueError as e:
            print(f"Account creation failed: {e}")
            validate = False
        if validate is True:
            user = await dbm.run(lambda: dbm.create_record(
            dbm.models["Users"],
            username=self.username,
            user_fname=self.fname,
            user_email=self.email,
            user_dob=self.dob,
            user_password=hashlib.sha256(self.password.encode('utf-8')).hexdigest()
            ))
    
    async def readAccount(self, value):
        user = await dbm.run(lambda: dbm.read_record(dbm.models["Users"], value))
        if user is None:
            print("This User Doesn't Exist")
            return None
        else:
            print("Fetched User:", user.username,user.user_fname, user.user_email, user.user_dob)
            return user
    
    async def readAllUsers(self):
        Users = await dbm.run(lambda: list(dbm.models["Users"].select()))
        if not Users:
            print("No users found")
            return []
        for u in Users:
            print(u.user_id, u.username, u.user_fname, u.user_email, u.user_dob)
        return Users

    def login(self,username, password):
        user = asyncio.run(self.readAccount(username))
        if user and user.user_password == hashlib.sha256(password.encode('utf-8')).hexdigest():
            self.currentuser = username
            print(f"Hello: {username}")
            print(user.username, user.user_email, user.user_dob)
            return True
        else:
            print("Invalid username or password")
            return False

    def logout(self):
        self.currentUser = "Guest"
        return self.login()
        #sets to guest so when logged out information can not be accessed

    async def deleteAccount(self, userid):
        user = await dbm.run(lambda: dbm.delete_record(dbm.models["Users"], userid))
        if user is None:
            print("This User Doesn't Exist")
        

    async def updateEmail(self, userid, new_email):
        user = await dbm.run(lambda: dbm.update_record(dbm.models["Users"], userid, user_email=new_email))
        if user is None:
            print("This User Doesn't Exist")
            return
   
    async def updatePassword(self, userid, new_password):
        user = await dbm.run(lambda: dbm.update_record(dbm.models["Users"], userid, user_password=new_password))
        if user is None:
            print("This User Doesn't Exist")
            return

    def sync():
        # Sync current user account to db, can be left for later
        pass

class UserRoutines:
    def __init__(self, user_id, rout_id):
        self.user_id = user_id
        self.rout_id = rout_id

    async def addRoutine(self, user_id, rout_id):
        user = await dbm.run(lambda: dbm.read_record(dbm.models["Users"], user_id))
        routine = await dbm.run(lambda: dbm.read_record(dbm.models["Routines"], rout_id))
        if user is None:
            print("This User Doesn't Exist")
            return
        if routine is None:
            print("This Routine Doesn't Exist")
            return
        await dbm.run(lambda: dbm.create_record(
            dbm.models["UserRoutines"],
            user_id=user_id,
            rout_id=rout_id
        ))

 
if __name__ == "__main__": 
    account_manager = AccountManager(str(time.time())+"@example.com", "exampleuser", "Example", date(2000, 1, 1), "password123")
    asyncio.run(account_manager.readAllUsers())
    #asyncio.run(account_manager.readAccount())
    #asyncio.run(account_manager.createAccount())
    #asyncio.run(account_manager.deleteAccount())
    asyncio.run(account_manager.updateEmail(10, "thegoblin1@example.com"))
    asyncio.run(account_manager.updatePassword(10, "newpassword123"))
