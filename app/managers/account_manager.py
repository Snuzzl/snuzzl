import hashlib
from datetime import datetime, date, timedelta

class AccountManager:
    def __init__(self, db):
        self.dbm = db
        self.users_table = self.dbm.models["Users"]

        # Tables for account creation and deletion
        self.metrics_table = self.dbm.models["Metrics"]
        self.metric_value_table = self.dbm.models["MetricValue"]
        self.challenges_table = self.dbm.models["Challenges"]
        self.user_challenges_table = self.dbm.models["UserChallenges"]
        self.user_reward_table = self.dbm.models["UserRewards"]
        self.user_task_table = self.dbm.models["UserTask"]
        self.user_routine_table = self.dbm.models["UserRoutine"]
        self.friends_table = self.dbm.models["Friends"]
        self.comp_participant_table = self.dbm.models["CompParticipant"]


    def _validate_username(self, username):
        if not username or len(username) > 30 or len(username) < 5:
            raise ValueError("Username must be at between 5 and 30 characters long")
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
    
    def _validate_fname(self, fname):
        if not fname or len(fname) > 20 or len(fname) < 3:
            raise ValueError("First name must be at between 3 and 20 characters long")
        if not fname.isalpha():
            raise ValueError("First name can only contain letters")
        return True
    
    def _validate_dob(self, dob):
        try:
            datetime.strptime(dob, "%Y-%m-%d")
            return True
        except ValueError:
            raise ValueError("Date must be in valid format")

    def create_account(self, username, password, fname, email, dob):
        if self.user_info(username=username):
            return {'success': False, 'message': "Account creation failed: Username already exists"}
        try:
            if self._validate_username(username) and self._validate_email(email) and self._validate_fname(fname) and self._validate_dob(dob):
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

    def user_info(self, username=None, user_id=None):
        try: 
            if user_id:
                user = self.users_table.get(self.users_table.user_id == user_id)
            else:
                user = self.users_table.get(self.users_table.username == username)
        except Exception:
            return None
        return {
            'success': True,
            'user id': user.user_id,
            'username': user.username,
            'email': user.user_email,
            'fname': user.user_fname,
            'dob': user.user_dob,
            'password': user.user_password
            } 

    def delete_account(self, user_id):
        # Check user exists
        if self.dbm.read_record(self.users_table, user_id):
            # First delete all records associated with user_id
            self.metric_value_table.delete().where(self.metric_value_table.user_id == user_id).execute()
            self.user_challenges_table.delete().where(self.user_challenges_table.user_id == user_id).execute()
            self.user_reward_table.delete().where(self.user_reward_table.user_id == user_id).execute()
            self.user_task_table.delete().where(self.user_task_table.user_id == user_id).execute()
            self.user_routine_table.delete().where(self.user_routine_table.user_id == user_id).execute()
            self.friends_table.delete().where(self.friends_table.user_id == user_id).execute()
            self.comp_participant_table.delete().where(self.comp_participant_table.user_id == user_id).execute()

            # Then delete the user
            user = self.dbm.delete_record(self.users_table, user_id)
            if user == 1:
                return {'success': True, 'message': f"User ID {user_id} was deleted"}
            elif user == 0:
                return {'success': False, 'message': f"Failed to delete user ID {user_id}"}
        return {'success': False, 'message': f"User ID {user_id} does not exist"}

    def update_username(self, user_id, new_username):
        try:
            if self._validate_username(new_username):
                user = self.dbm.update_record(self.users_table, user_id, username=new_username)
        except Exception as e:
            return {'success': False, 'message': f"Username update failed: {e}"}
        if user is None:
            return {'success': False, 'message': f"User ID {user_id} does not exist"}
        return {'success': True, 'message': "Username updated"}

    def update_email(self, user_id, new_email):
        try:
            if self._validate_email(new_email):
                user = self.dbm.update_record(self.users_table, user_id, user_email=new_email)
        except Exception as e:
            return {'success': False, 'message': f"Email update failed: {e}"}
        if user is None:
            return {'success': False, 'message': f"User ID {user_id} does not exist"}
        return {'success': True, 'message': f"Email updated"}
   
    def update_password(self, user_id, new_password):
        try:
            user = self.dbm.update_record(self.users_table, user_id, user_password=new_password)
        except Exception as e:
            return {'success': False, 'message': f"Password update failed: {e}"}
        if user is None:
            return {'success': False, 'message': f"User ID {user_id} does not exist"}
        return {'success': True, 'message': "Password updated"}
    
    def login(self, username, password):
        user = self.user_info(username=username)
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