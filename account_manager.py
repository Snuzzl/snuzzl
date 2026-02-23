class AccountManager:   
    def __init__(self):
        self.username = None
        self.currentUser = "Guest"
        self.accounts = []

    def login(self):
        # If username and hashed password match the values in db then self.currentUser = username
        # Password can be worked out later
        #new log in systme will have to be made to work with hashing and db
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

    def createAccount(self, account):
        self.accounts.append(account)
        self.username = account.username
        self.currentUser = account.username
        print(f"Account '{account.username}' created and added to list")
        #the user information is stored like htis for now for testing 

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

    def get_all_accounts(self):
        return [acc.username for acc in self.accounts]

    def print_all_accounts(self):
        print("=== All Accounts ===")
        for account in self.accounts:
            print(f"- {account.username} ({account.email})")
        print()

class Account:
    #validates all inputs
    # thought it was cleaner within a seperate class but can be moved to account manager if needed

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

    account_manager.print_all_accounts()
    account_manager.updateEmail()
    account_manager.updatePassword()

if __name__ == "__main__":    
    run()