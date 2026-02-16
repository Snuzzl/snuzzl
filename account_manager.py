class Account:
    def __init__(self, username):
        # Representation from system requirements
        # Validate values according to valid/invalid representations
        self.username = self._validateUsername(username)
        pass

    def _validateUsername(username):
        pass


class AccountManager:
    
    def __init__(self):
        self.currentUser = "Guest"

    def login(self, username, password):
        # If username and hashed password match the values in db then self.currentUser = username
        # Password can be worked out later
        pass

    def logout(self):
        self.currentUser = "Guest"
        # Return to login page in UI

    def createAccount(self, username):
        pass
    
    def deleteAccount(self, username):
        pass

    def updateEmail():
        pass

    def updatePasword():
        pass

    def sync():
        # Sync current user account to db, can be left for later
        pass
