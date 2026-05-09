import asyncio
from datetime import *
import hashlib
from app.db.database_manager import DatabaseManager

dbm = DatabaseManager()


class AccountManager:
    """Manages user account creation, validation, and database operations.

    Attributes:
        email (str): User's email address.
        username (str): User's chosen username.
        fname (str): User's first name.
        dob (date): User's date of birth.
        password (str): User's plaintext password.
    """

    def __init__(self, email, username, fname, dob, password):
        """Initializes an AccountManager instance.

        Args:
            email (str): User's email.
            username (str): Username.
            fname (str): First name.
            dob (date): Date of birth.
            password (str): Password.
        """
        self.username = username
        self.email = email
        self.fname = fname
        self.dob = dob
        self.password = password

    async def _validateUsername(self, username):
        """Validates the username format.

        Args:
            username (str): Username to validate.

        Raises:
            ValueError: If username is too short or contains invalid characters.

        Returns:
            str: Validated username.
        """
        if not username or len(username) < 3:
            raise ValueError("Username must be at least 3 characters long")
        if not username.isalnum():
            raise ValueError("Username can only contain letters and numbers")
        return username

    def _validateEmail(self, email):
        """Validates the email format.

        Args:
            email (str): Email to validate.

        Raises:
            ValueError: If email format is invalid.

        Returns:
            str: Validated email.
        """
        if "@" not in email or "." not in email.split("@")[1]:
            raise ValueError("Invalid email format")
        return email

    def _validatePassword(self, password):
        """Validates the password format.

        Args:
            password (str): Password to validate.

        Raises:
            ValueError: If password is too short.

        Returns:
            str: Validated password.
        """
        if not password or len(password) < 6:
            raise ValueError("Password must be at least 6 characters long")
        return password

    async def createAccount(self):
        """Creates a new user account after validation.

        Validates username, email, and password.  
        If valid, inserts a new user record into the database.

        Returns:
            None
        """
        try:
            validate_username = await self._validateUsername(self.username)
            validate_email = self._validateEmail(self.email)
            validate_password = self._validatePassword(self.password)
            validate = True
        except ValueError as e:
            print(f"Account creation failed: {e}")
            validate = False

        if validate is True:
            await dbm.run(lambda: dbm.create_record(
                dbm.models["Users"],
                username=self.username,
                user_fname=self.fname,
                user_email=self.email,
                user_dob=self.dob,
                user_password=hashlib.sha256(self.password.encode('utf-8')).hexdigest()
            ))

    async def userInfo(self, username):
        """Loads user information into the current instance.

        Args:
            username (str): Username to fetch.

        Returns:
            None
        """
        Users = await dbm.run(lambda: list(dbm.models["Users"].select()))
        for u in Users:
            if u.username == self.username:
                break

        self.fname = u.fname
        self.email = u.email
        self.password = u.password
        self.dob = u.dob
        print("Summary Init:", self.username, self.fname, self.email, self.password, self.dob)

    async def readAccount(self, value):
        """Reads a single user account from the database.

        Args:
            value (Any): Primary key or lookup value.

        Returns:
            User | None: The user record if found, otherwise None.
        """
        user = await dbm.run(lambda: dbm.read_record(dbm.models["Users"], value))
        if user is None:
            print("This User Doesn't Exist")
            return None
        else:
            print("Fetched User:", user.username, user.user_fname, user.user_email, user.user_dob)
            return user

    async def readAllUsers(self):
        """Reads and prints all users from the database.

        Returns:
            list: List of all user records.
        """
        Users = await dbm.run(lambda: list(dbm.models["Users"].select()))
        if not Users:
            print("No users found")
            return []

        for u in Users:
            print(u.user_id, u.username, u.user_fname, u.user_email, u.user_dob)

        return Users

    async def deleteAccount(self, userid):
        """Deletes a user account.

        Args:
            userid (int): User ID to delete.

        Returns:
            None
        """
        user = await dbm.run(lambda: dbm.delete_record(dbm.models["Users"], userid))
        if user is None:
            print("This User Doesn't Exist")

    async def updateEmail(self, userid, new_email):
        """Updates a user's email.

        Args:
            userid (int): User ID.
            new_email (str): New email address.

        Returns:
            None
        """
        user = await dbm.run(lambda: dbm.update_record(dbm.models["Users"], userid, user_email=new_email))
        if user is None:
            print("This User Doesn't Exist")

    async def updatePassword(self, userid, new_password):
        """Updates a user's password.

        Args:
            userid (int): User ID.
            new_password (str): New plaintext password.

        Returns:
            None
        """
        new_password = hashlib.sha256(new_password.encode('utf-8')).hexdigest()
        user = await dbm.run(lambda: dbm.update_record(dbm.models["Users"], userid, user_password=new_password))
        if user is None:
            print("This User Doesn't Exist")

    def sync():
        """Synchronizes the current user account to the database.

        Note:
            This function is currently a placeholder.

        Returns:
            None
        """
        pass


class login:
    """Handles user login authentication."""

    def __init__(self, username, password):
        """Initializes a login instance.

        Args:
            username (str): Username.
            password (str): Password.
        """
        self.username = username
        self.password = password

    async def userLogin(self):
        """Attempts to authenticate a user.

        Returns:
            dict: Login result containing success status and user data or error message.
        """
        Users = await dbm.run(lambda: list(dbm.models["Users"].select()))
        for u in Users:
            if u.username == self.username:
                break

        if u.username == self.username:
            if u.user_password == hashlib.sha256(self.password.encode('utf-8')).hexdigest():
                self.currentuser = self.username
                print(f"Hello: {self.username}")
                print(u.username, u.user_email, u.user_dob)
                return {
                    'success': True,
                    'username': u.username,
                    'email': u.user_email,
                    'fname': u.user_fname,
                    'dob': u.user_dob,
                    'user_id': u.user_id
                }
            else:
                print("Incorrect password")
                return {'success': False, 'message': "Incorrect password"}
        else:
            print("Invalid username")
            return {'success': False, 'message': "Invalid username"}


if __name__ == "__main__":
    account_manager = AccountManager(
        "testemail1@example.com",
        "exampleuser",
        "Example",
        date(2000, 1, 1),
        "Password123!"
    )
    asyncio.run(account_manager.readAllUsers())