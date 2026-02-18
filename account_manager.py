class AccountManager:   
    def __init__(self):
        self.username = None
        self.currentUser = "Guest"
        self.accounts = []

    def login(self):
        # If username and hashed password match the values in db then self.currentUser = username
        # Password can be worked out later
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
        return self.login()

    def createAccount(self, account):
        self.accounts.append(account)
        self.username = account.username
        self.currentUser = account.username
        print(f"Account '{account.username}' created and added to list")
 
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

    def updateEmail():
        pass

    def updatePasword():
        pass

    def sync():
        # Sync current user account to db, can be left for later
        pass

    def get_all_accounts(self):
        return [acc.username for acc in self.accounts]

    def print_all_accounts(self):
        print("=== All Accounts ===")
        for account in self.accounts:
            print(f"- {account.username} ({account.email})")
        print()


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

    def __str__(self):
        return f"Username: {self.username}\nEmail: {self.email}\nActive: {self.is_active}"

    def print_details(self):
        print(self)




#testing
def run():
    account_manager = AccountManager()
    
    # Create accounts
    account1 = Account("test1", "test1@example.com", "test123")
    account_manager.createAccount(account1)
    account1.print_details()
    
    account2 = Account("admin", "admin@example.com", "admin123")
    account_manager.createAccount(account2)
    account2.print_details()
    
    account3 = Account("user2", "user2@example.com", "pass456")
    account_manager.createAccount(account3)
    
    # Print all accounts
    account_manager.print_all_accounts()
    
    # Delete an account
    print("Deleting test1")
    account_manager.deleteAccount("test1")
    
    #pritning accounts
    account_manager.print_all_accounts()
    print("All usernames:", account_manager.get_all_accounts())

    #test for deleting a none existent account
    account_manager.deleteAccount("test1")
    account_manager.print_all_accounts()


    #login test
    print("Logging in as admin")
    account_manager.login()

    #test log out
    print("Logging out")
    account_manager.logout()

    #test logging back in
    print("Logging out")
    account_manager.logout()

if __name__ == "__main__":    
    run()