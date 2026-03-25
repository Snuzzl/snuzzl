import asyncio
from peewee import *
from datetime import *
import hashlib
from database_manager import DatabaseManager
from database_models import Users

dbm = DatabaseManager()

class AccountManager:
    def __init__(self,email, username, fname, dob, password):
        self.username = username
        self.email = email
        self.fname = fname
        self.dob = dob
        self.password = password
        self.currentuser = "Guest"

    def _validateUsername(self, username):
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
        self.password = hashlib.sha256(password.encode('utf-8')).hexdigest()
        return password

    async def createAccount(self):
        try:
            validate_username = self._validateUsername(self.username)
            validate_email = self._validateEmail(self.email)
            validate_password = self._validatePassword(self.password)
            validate = True
        except ValueError as e:
            print(f"Account creation failed: {e}")
            validate = False
        if validate is True:
            print(self.password)
            user = await dbm.run(lambda: dbm.create_record(
            dbm.models["Users"],
            username=self.username,
            user_fname=self.fname,
            user_email=self.email,
            user_dob=self.dob,
            user_password=self.password
            ))

    async def readAccount(self, value):
        user = await dbm.run(lambda: dbm.read_record(dbm.models["Users"], value))
        if user is None:
            print("This User Doesn't Exist")
        else:
            print("Fetched User:", user.username,user.fname, user.user_email, user.user_dob)

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
        self.currentuser = "Guest"
       
        #sets to guest so when logged out information can not be accessed

    async def deleteAccount(self, value):
        user = await dbm.run(lambda: dbm.delete_record(dbm.models["Users"], value))
        if user is None:
            print("This User Doesn't Exist")
            return
        print("Deleted User")

    def updateEmail(self, account):
        new_email = input("Enter new email: ")
        account.email = new_email
        print(f"Email updated to {new_email}")
        return True
   
    def updatePassword(self):
        password = input("Enter current password: ")
        if account.password == password:
            new_password = input("Enter new password: ")
            for account in self.accounts:
                if account.username == self.currentUser:
                    account.password = new_password
                    print(f"Password updated to {new_password}")
                    return True
        else:
            print("Incorrect current password")
            return False

    def sync():
        # Sync current user account to db, can be left for later
        pass
 
if __name__ == "__main__": 
    account_manager = AccountManager("test99@example.com","testuser99", "Example99",date(2000, 1, 1),"password99")
    #asyncio.run(account_manager.createAccount())
    asyncio.run(account_manager.login("testuser99", "password99"))