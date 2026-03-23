import asyncio
from datetime import *
from database_manager import DatabaseManager
from database_models import Users

dbm = DatabaseManager()

class AccountManager:
    def __init__(self,email,username,fname,dob,password):
        self.username = username
        self.email = email
        self.fname = fname
        self.dob = dob
        self.password = password

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
            user = await dbm.run(lambda: dbm.create_record(
            dbm.models["Users"],
            username=self.username,
            user_fname=self.fname,
            user_email=self.email,
            user_dob=self.dob
            ))
    
    async def readAccount(self, username):
        user = await dbm.run(lambda: dbm.read_record(dbm.models["Users"], 9))
        if user is None:
            print("This User Doesn't Exist")
        else:
            print("Fetched User:", user.username)

    def login(self):
        print("---Login Page---")
        username = input("Enter username: ")
        password = input("Enter password: ")
        for account in self.accounts:
            if account.username == username and account.password == password:
                self.currentUser = username
                print(f"Hello: {username}")
                print(account)
                return True
            else:
                print("Invalid username or password")
                return False
        pass

    def logout(self):
        self.currentUser = "Guest"
        return self.login()
        #sets to guest so when logged out information can not be accessed

    def deleteAccount(self, username):
        for i, account in enumerate(self.accounts):
            if account.username == username:
                self.accounts.pop(i)
                print(f"Account '{username}' deleted successfully")
                if self.currentUser == username:
                    self.currentUser = "Guest"
                return True
        print(f"Account '{username}' not found")
        return False

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
    account_manager = AccountManager("example@example.com","exampleuser", "Example",date(2000, 1, 1),"password123")
    account_manager.createAccount()