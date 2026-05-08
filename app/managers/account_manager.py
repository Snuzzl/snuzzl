import hashlib

class AccountManager:
    def __init__(self, db, email,username,fname,dob,password):
        self.dbm = db
        self.users_table = self.dbm.models["Users"]
        self.username = username
        self.email = email
        self.fname = fname
        self.dob = dob
        self.password = password


    def _validate_username(self, username):
        if not username or len(username) < 3:
            raise ValueError("Username must be at least 3 characters long")
        if not username.isalnum():
            raise ValueError("Username can only contain letters and numbers")
        return True

    def _validate_email(self, email):
        if "@" not in email or "." not in email.split("@")[1]:
            raise ValueError("Invalid email format")
        return True

    async def create_account(self, username, password, fname, email, dob):
        try:
            if self._validate_username(username) and self._validate_email(email):
                self.dbm.create_record(
                    self.users_table,
                    username=username,
                    user_fname=fname,
                    user_email=email,
                    user_dob=dob,
                    user_password=password
                )
        except Exception as e:
            return {'message' : f"Account creation failed: {e}"}

    
    async def userInfo(self, username):
        Users = await self.dbm.run(lambda: list(self.dbm.models["Users"].select()))
        for u in Users:
                if u.username == self.username:
                    break
        self.fname = u.fname 
        self.email = u.email 
        self.password = u.password 
        self.dob = u.dob
        print("Summary Init:", self.username, self.fname, self.email, self.password, self.dob)
    
    async def readAccount(self, value):
        user = await self.dbm.run(lambda: self.dbm.read_record(self.dbm.models["Users"], value))
        if user is None:
            print("This User Doesn't Exist")
            return None
        else:
            print("Fetched User:", user.username,user.user_fname, user.user_email, user.user_dob)
            return user
    
    async def readAllUsers(self):
        Users = await self.dbm.run(lambda: list(self.dbm.models["Users"].select()))
        if not Users:
            print("No users found")
            return []
        for u in Users:
            print(u.user_id, u.username, u.user_fname, u.user_email, u.user_dob)
        return Users

    async def deleteAccount(self, userid):
        user = await self.dbm.run(lambda: self.dbm.delete_record(self.dbm.models["Users"], userid))
        if user is None:
            print("This User Doesn't Exist")
        

    async def updateEmail(self, userid, new_email):
        user = await self.dbm.run(lambda: self.dbm.update_record(self.dbm.models["Users"], userid, user_email=new_email))
        if user is None:
            print("This User Doesn't Exist")
            return
   
    async def updatePassword(self, userid, new_password):
        new_password = hashlib.sha256(new_password.encode('utf-8')).hexdigest()
        user = await self.dbm.run(lambda: self.dbm.update_record(self.dbm.models["Users"], userid, user_password=new_password))
        if user is None:
            print("This User Doesn't Exist")
            return
    
    def login(self, username, password):
        user = (
            self.users_table
            .select()
            .where(self.users_table.username == username)
            )

        # If user exists, check password
        if user:
            if user.user_password == password:
                # Return user data as dictionary
                return {
                    'success': True,
                    'username': user.username,
                    'email': user.user_email,
                    'fname': user.user_fname,
                    'dob': user.user_dob,
                    'user_id': user.user_id
                    }
        # Return error message when if statements are false
        return {'success': False, 'message': "Incorrect username or password"}