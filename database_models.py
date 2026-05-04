from peewee import *
from database_connection import db

class BaseModel(Model):
    class Meta:
        database = db

#----- New Tables -----#

class RewardType(BaseModel):
    type_id = AutoField()
    type_name = CharField(30)
    type_desc = CharField(100, null=True)
    class Meta:
        table_name = "rewardtype"

class MetType(BaseModel):
    type_id = AutoField()
    type_name = CharField(30)
    type_desc = CharField(100, null=True)
    class Meta:
        table_name = "mettype"

class RoutFreq(BaseModel):
    freq_id = AutoField()
    freq_name = CharField(30)
    freq_desc = CharField(100, null=True)
    class Meta:
        table_name = "routfreq"

class TaskType(BaseModel):
    type_id = AutoField()
    type_name = CharField(20)
    type_desc = CharField(200)
    class Meta:
        table_name = "tasktype"

#----- Main Tables -----#

class Users(BaseModel):
    user_id = AutoField()
    username = CharField(30, unique=True)
    user_fname = CharField(20)
    user_email = CharField(100, unique=True)
    user_dob = DateField()
    user_password = TextField(unique=True)
    class Meta:
        table_name = "users"

class Tasks(BaseModel):
    task_id = AutoField()
    task_name = CharField(20)
    task_desc = CharField(250, null=True)
    type_id = ForeignKeyField(TaskType, backref="tasks", column_name="type_id")
    class Meta:
        table_name = "tasks"

class CustomTasks(BaseModel):
    cust_id = AutoField()
    cust_name = CharField(20)
    cust_desc = CharField(200, null=True)
    type_id = ForeignKeyField(TaskType, backref="customtasks", column_name="type_id")
    class Meta:
        table_name = "customtasks"

class Routines(BaseModel):
    rout_id = AutoField()
    rout_name = CharField(20)
    class Meta:
        table_name = "routines"

class Reminders(BaseModel):
    reminder_id = AutoField()
    task_id = ForeignKeyField(Tasks, backref="reminders", column_name="task_id")
    reminder_txt = CharField(100, null=True)
    remind_at = TimestampField()
    class Meta:
        table_name = "reminders"

class Metrics(BaseModel):
    met_id = AutoField()
    met_name = CharField(20)
    met_desc = CharField(250, null=True)
    met_min = SmallIntegerField()
    met_max = SmallIntegerField()
    met_type = ForeignKeyField(MetType, backref="metrics", column_name="met_type")
    class Meta:
        table_name = "metrics"

class MetricValue(BaseModel):
    metval_id = AutoField()
    user_id = ForeignKeyField(Users, backref="metricvalue", column_name="user_id")
    met_id = ForeignKeyField(Metrics, backref="metricvalue", column_name="met_id")
    metval_date = DateField()
    metval_val = SmallIntegerField()
    class Meta:
        table_name = "metricvalue"

class Libraries(BaseModel):
    libr_id = AutoField()
    libr_name = CharField(50)
    libr_desc = CharField(250, null=True)
    libr_created_date = DateField()
    class Meta:
        table_name = "libraries"

class Exercises(BaseModel):
    exe_id = AutoField()
    exe_name = CharField(50)
    exe_length = IntegerField() 
    # Need to convert into seconds/minutes and then convert it back
    # idk dont blame me
    exe_kcal = IntegerField()
    class Meta:
        table_name = "exercises"

class Communities(BaseModel):
    comm_id = AutoField()
    comm_name = CharField(50)
    comm_date_created = DateField()
    class Meta:
        table_name = "communities"    

class Challenges(BaseModel):
    chall_id = AutoField()
    chall_name = CharField(50)
    chall_desc = CharField(200, null=True)
    class Meta:
        table_name = "challenges"

class Rewards(BaseModel):
    reward_id = AutoField()
    chall_id = ForeignKeyField(Challenges, backref="rewards", column_name="chall_id")
    reward_name = CharField(50)
    reward_type = ForeignKeyField(RewardType, backref="rewards", column_name="reward_type")
    class Meta:
        table_name = "rewards"

class Competitions(BaseModel):
    comp_id = AutoField()
    comp_name = CharField(50)
    comp_sdate = DateField()
    comp_edate = DateField()
    class Meta:
        table_name = "competitions"

class Friends(BaseModel):
    user_id = ForeignKeyField(Users, backref="friends_user", column_name="user_id")
    friend_id = ForeignKeyField(Users, backref="friends_friend", column_name="friend_id")
    friend_status = CharField(20)

    class Meta:
        table_name = "friends"
        primary_key = CompositeKey('user_id', 'friend_id')
        constraints = [Check('user_id <> friend_id')]
    

#----- Intersection Tables -----#

class UserRoutine(BaseModel):
    user_id = ForeignKeyField(Users, backref="userroutine", column_name="user_id")
    rout_id = ForeignKeyField(Routines, backref="userroutine", column_name="rout_id")
    rout_freq = ForeignKeyField(RoutFreq, backref="routines", column_name="rout_freq")
    class Meta:
        table_name = "userroutine"
        primary_key = CompositeKey('user_id','rout_id')

class UserTask(BaseModel):
    user_id = ForeignKeyField(Users, column_name="user_id")
    task_id = ForeignKeyField(Tasks, column_name="task_id", null=True)
    cust_id = ForeignKeyField(CustomTasks, column_name="cust_id", null=True)
    task_complete = BooleanField()
    task_date = DateField()
    task_stime = TimeField()
    task_etime = TimeField()
    class Meta:
        table_name = "usertask"
        primary_key = CompositeKey('user_id', 'task_id')

class UserChallenges(BaseModel):
    user_id = ForeignKeyField(Users, backref="userchallenges", column_name="user_id")
    chall_id = ForeignKeyField(Challenges, backref="userchallenges", column_name="chall_id")
    chall_sdate = DateField()
    chall_edate = DateField()
    class Meta:
        table_name = "userchallenges"
        primary_key = CompositeKey('user_id','chall_id')

class CompParticipant(BaseModel):
    user_id = ForeignKeyField(Users, backref="compparticipant", column_name="user_id")
    comp_id = ForeignKeyField(Competitions, backref="compparticipant", column_name="comp_id")
    class Meta:
        table_name = "compparticipant"
        primary_key = CompositeKey('user_id','comp_id')

class CommunityMembers(BaseModel):
    user_id = ForeignKeyField(Users, backref="communitymembers", column_name="user_id")
    comm_id = ForeignKeyField(Communities, backref="communitymembers", column_name="comm_id")
    class Meta:
        table_name = "communitymembers"
        primary_key = CompositeKey('user_id','comm_id')

class UserLibrary(BaseModel):
    user_id = ForeignKeyField(Users, backref="userlibrary", column_name="user_id")
    libr_id = ForeignKeyField(Libraries, backref="userlibrary", column_name="libr_id")
    class Meta:
        table_name = "userlibrary"
        primary_key = CompositeKey('user_id','libr_id')

class ExerciseLibrary(BaseModel):
    exe_id = ForeignKeyField(Exercises, backref="exerciselibrary", column_name="exe_id")
    libr_id = ForeignKeyField(Libraries, backref="exerciselibrary", column_name="libr_id")
    class Meta:
        table_name = "exerciselibrary"
        primary_key = CompositeKey('exe_id','libr_id')

class TaskChallenges(BaseModel):
    task_id = ForeignKeyField(Tasks, backref="taskchallenges", column_name="task_id")
    chall_id = ForeignKeyField(Challenges, backref="taskchallenges", column_name="chall_id")
    class Meta:
        table_name = "taskchallenges"
        primary_key = CompositeKey('task_id','chall_id')

class CompChallenges(BaseModel):
    comp_id = ForeignKeyField(Competitions, backref="compchallenges", column_name="comp_id")
    chall_id = ForeignKeyField(Challenges, backref="compchallenges", column_name="chall_id")
    class Meta:
        table_name = "compchallenges"
        primary_key = CompositeKey('comp_id','chall_id')

class TaskMetric(BaseModel):
    task_id = ForeignKeyField(Tasks, backref="taskmetric", column_name="task_id")
    met_id = ForeignKeyField(Metrics, backref="taskmetric", column_name="met_id")
    class Meta:
        table_name = "taskmetric"
        primary_key = CompositeKey('task_id','met_id')

class RoutineTask(BaseModel):
    routinetask_id = AutoField()
    rout_id = ForeignKeyField(Routines, backref="routinetask", column_name="rout_id")
    task_id = ForeignKeyField(Tasks, backref="routinetask", column_name="task_id", null=True)
    cust_id = ForeignKeyField(CustomTasks, backref="routinetask", column_name="cust_id", null=True)
    class Meta:
        table_name = "routinetask"

class UserRewards(BaseModel):
    user_id = ForeignKeyField(Rewards, backref="userrewards", column_name="user_id")
    reward_id = ForeignKeyField(Rewards, backref="userrewards", column_name="reward_id")
    reward_status = CharField()
    class Meta:
        table_name = "userrewards"

dbmodel_list = {"rewardType": RewardType,
        "metType": MetType,
        "routFreq": RoutFreq,
        "TaskType": TaskType,
        "Users": Users,
        "Tasks": Tasks,
        "CustomTasks": CustomTasks,
        "Routines": Routines,
        "Reminders": Reminders,
        "Metrics": Metrics,
        "MetricValue": MetricValue,
        "Libraries": Libraries,
        "Exercises": Exercises,
        "Communities": Communities,
        "Challenges": Challenges,
        "Rewards": Rewards,
        "Competitions": Competitions,
        "Friends": Friends,
        "UserRoutine": UserRoutine,
        "UserTask": UserTask,
        "UserChallenges": UserChallenges,
        "CompParticipant": CompParticipant,
        "CommunityMembers": CommunityMembers,
        "UserLibrary": UserLibrary,
        "ExerciseLibrary": ExerciseLibrary,
        "TaskChallenges": TaskChallenges,
        "CompChallenges": CompChallenges,
        "TaskMetric": TaskMetric,
        "RoutineTask": RoutineTask,
        "UserRewards": UserRewards
        }