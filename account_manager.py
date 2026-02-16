

class AccountManager:
    
    def __init__(self):
        self.username = None
        self.currentUser = "Guest"

    def login(self, username, password):
        # If username and hashed password match the values in db then self.currentUser = username
        # Password can be worked out later
        pass

    def logout(self):
        self.currentUser = "Guest"
        # Return to login page in UI

    def createAccount(self, username):
        self.username = username
        self.currentUser = username
    
    def deleteAccount(self, username):
        pass

    def updateEmail():
        pass

    def updatePasword():
        pass

    def sync():
        # Sync current user account to db, can be left for later
        pass

class Account:
    def __init__(self, username, email, password):
        self.username = self._validateUsername(username)
        self.email = self._validateEmail(email)
        self.password = self._validatePassword(password)
        self.is_active = True

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

    def create_account(self, username, email, password):
        try:
            self.username = self._validateUsername(username)
            self.email = self._validateEmail(email)
            self.password = self._validatePassword(password)
            self.is_active = True
            return True
        except ValueError as e:
            print(f"Account creation failed: {e}")
            return False

    def __str__(self):
        return f"Username: {self.username}\nEmail: {self.email}\nActive: {self.is_active}"

    def print_details(self):
        print(self)


def run():
    account_manager = AccountManager()
    account = Account("graceloveslivemusic", "gracie_bear@example.com", "wolfiealice123")
    account = Account("theleader", "example@example.com", "mrnegative123")
    account_manager.createAccount(account.username)
    account.print_details()

if __name__ == "__main__":    
    run()