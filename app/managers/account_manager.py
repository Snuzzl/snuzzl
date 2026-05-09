import hashlib
from datetime import date, timedelta

class AccountManager:
    def __init__(self, db):
        self.dbm = db
        self.users_table = self.dbm.models["Users"]

        # Tables for account creation and deletion
        self.metrics_table = self.dbm.models["Metrics"]
        self.metric_value_table = self.dbm.models["MetricValue"]
        self.challenges_table = self.dbm.models["Challenges"]
        self.user_challenges_table = self.dbm.models["UserChallenges"]

    def _validate_username(self, username):
        if not username or len(username) < 3:
            raise ValueError("Username must be at least 3 characters long")
        if not username.isalnum():
            raise ValueError("Username can only contain letters and numbers")
        # Check that username has at least 1 letter in it
        for c in range(len(username) + 1):
            if c == len(username):
                raise ValueError("Username must contain at least one letter.")
            try:
                int(username[c])
            except ValueError:
                return True

    def _validate_email(self, email):
        if "@" not in email or "." not in email.split("@")[1]:
            raise ValueError("Invalid email format")
        return True

    def create_account(self, username, password, fname, email, dob):
        if self.user_info(username):
            return {'success': False, 'message': "Account creation failed: Username already exists"}
        try:
            if self._validate_username(username) and self._validate_email(email):
                user = self.dbm.create_record(
                    self.users_table,
                    username=username,
                    user_fname=fname,
                    user_email=email,
                    user_dob=dob,
                    user_password=password
                )
            self.assign_default_metrics(user.user_id)
            self.assign_default_challenges(user.user_id)
            return {'success': True, 'user_id': user.user_id}
        except Exception as e:
            return {'success': False, 'message': f"Account creation failed: {e}"}

    def assign_default_metrics(self, user_id):
        default_value = 0
        system_metrics = self.metrics_table.select()
        for metric in system_metrics:
            self.dbm.create_record(
                self.metric_value_table, 
                user_id=user_id, 
                met_id=metric.met_id, 
                metval_date=date.today(),
                metval_val=default_value
            )

    def assign_default_challenges(self, user_id):
        system_challenges = self.challenges_table.select()
        for challenge in system_challenges:
            self.dbm.create_record(
                self.user_challenges_table,
                user_id=user_id,
                chall_id=challenge.chall_id,
                chall_sdate=date.today(),
                chall_edate=(date.today() + timedelta(days=7))
            )

    def user_info(self, username):
        try: 
            user = self.users_table.get(self.users_table.username == username)
        except Exception:
            return None
        return {
            'user id': user.user_id,
            'username': user.username,
            'email': user.user_email,
            'fname': user.user_fname,
            'dob': user.user_dob,
            'password': user.user_password
            } 

    def delete_account(self, user_id):
        user = self.dbm.delete_record(self.users_table, user_id)
        if user is None:
            print("This User Doesn't Exist")
        
    def update_email(self, user_id, new_email):
        user = self.dbm.update_record(self.users_table, user_id, user_email=new_email)
        if user is None:
            print("This User Doesn't Exist")
            return
   
    def update_password(self, user_id, new_password):
        new_password = hashlib.sha256(new_password.encode('utf-8')).hexdigest()
        user = self.dbm.update_record(self.users_table, user_id, user_password=new_password)
        if user is None:
            print("This User Doesn't Exist")
            return
    
    def login(self, username, password):
        user = self.user_info(username)
        # If user exists, check password
        if user:
            if user['password'] == password:
                # Return user data as dictionary
                return {
                    'success': True,
                    'user_id': user['user id']
                    }
        # Return error message when if statements are false
        return {'success': False, 'message': "Incorrect username or password"}    