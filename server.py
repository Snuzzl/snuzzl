from fastapi import FastAPI, HTTPException
from contextlib import asynccontextmanager
from fastapi.concurrency import run_in_threadpool
from pydantic import BaseModel
from app.db.database_connection import db
from app.db.database_manager import DatabaseManager
from app.db.database_models import UserChallenges, Challenges
from app.managers.task_manager import TaskManager
from app.managers.metric_manager import MetricManager
from app.managers.reward_manager import RewardManager
from app.managers.social_manager import SocialManager
from app.managers.account_manager import AccountManager

# Shared instances so the server and managers use one DB connection.
db_manager = DatabaseManager()
acc_mgr = AccountManager(db=db_manager)
task_mgr = TaskManager(db=db_manager)
metric_mgr = MetricManager(db=db_manager)
reward_mgr = RewardManager(database_manager=db_manager)
social_mgr = SocialManager(db=db_manager)


@asynccontextmanager
async def lifespan(app: FastAPI):
    db.connect()
    print("Database connected.")
    yield
    db.close()
    print("Database closed.")


app = FastAPI(lifespan=lifespan)


##### Account endpoints
class Login(BaseModel):
    username: str
    password: str

class Account(BaseModel):
    username: str 
    password: str 
    fname: str 
    email: str 
    dob: str 

class AccountUpdate(BaseModel):
    user_id: int
    username: str | None = None
    email: str | None = None
    password: str | None = None

@app.post("/login")
async def login(payload: Login):
    return await run_in_threadpool(acc_mgr.login, payload.username, payload.password)

@app.post("/create_account")
async def create_account(payload: Account):
    return await run_in_threadpool(acc_mgr.create_account, payload.username, payload.password, payload.fname, payload.email, payload.dob)

@app.get("/account/{user_id}")
async def account_info(user_id: int):
    account = await run_in_threadpool(acc_mgr.user_info, user_id=user_id)
    if account:
        return account
    return {'success': False, 'message': "Failed to retrieve account information"}

@app.post("/account/change_username")
async def change_username(payload: AccountUpdate):
    return await run_in_threadpool(acc_mgr.update_username, payload.user_id, payload.username)

@app.post("/account/change_email")
async def change_email(payload: AccountUpdate):
    return await run_in_threadpool(acc_mgr.update_email, payload.user_id, payload.email)

@app.post("/account/change_password")
async def change_password(payload: AccountUpdate):
    return await run_in_threadpool(acc_mgr.update_password, payload.user_id, payload.password)

@app.get("/account/{user_id}/delete")
async def delete_account(user_id: int):
    return await run_in_threadpool(acc_mgr.delete_account, user_id)

##### Task endpoints
# Request body schemas for endpoints that need structured input.
class CustomTaskCreate(BaseModel):
    name: str
    description: str | None = None


class CustomTaskAssign(BaseModel):
    cust_id: int
    date: str
    start_time: str
    end_time: str


class TaskUpdate(BaseModel):
    cust_name: str | None = None
    cust_desc: str | None = None
    task_date: str | None = None
    task_stime: str | None = None
    task_etime: str | None = None


class PredefinedAssign(BaseModel):
    task_id: int
    date: str
    start_time: str
    end_time: str


class PredefinedUpdate(BaseModel):
    task_date: str | None = None
    task_stime: str | None = None
    task_etime: str | None = None


class RewardCreate(BaseModel):
    chall_id: int
    reward_name: str
    reward_type: int


class UserRewardUpdate(BaseModel):
    reward_ids: list[int] | int | None = None
    reward_name: str | None = None
    reward_type: int | None = None


class RewardClaim(BaseModel):
    reward_id: int
    status: str = "Incomplete"


@app.get("/tasks/{user_id}")
async def get_tasks(user_id: int):
    tasks = await run_in_threadpool(task_mgr.get_tasks, user_id)
    # task_mgr.get_tasks already returns dicts with task_type field.
    return {"tasks": tasks}


@app.post("/tasks/{user_id}")
async def add_task(user_id: int, task: CustomTaskCreate):
    new_task = await run_in_threadpool(
        task_mgr.add_task, user_id, task.name, task.description
    )
    return {"cust_id": new_task.cust_id}


@app.post("/tasks/{user_id}/assign-custom")
async def assign_custom_task(user_id: int, body: CustomTaskAssign):
    await run_in_threadpool(
        task_mgr.assign_custom,
        user_id, body.cust_id, body.date, body.start_time, body.end_time
    )
    return {"assigned": True}


@app.delete("/tasks/{user_id}/{cust_id}")
async def delete_task(user_id: int, cust_id: int):
    await run_in_threadpool(task_mgr.remove_task, user_id, cust_id)
    return {"deleted": True}


@app.put("/tasks/{user_id}/{cust_id}/complete")
async def complete_task(user_id: int, cust_id: int):
    await run_in_threadpool(task_mgr.mark_complete, user_id, cust_id)
    return {"complete": True}


@app.put("/tasks/{user_id}/{cust_id}/incomplete")
async def incomplete_task(user_id: int, cust_id: int):
    await run_in_threadpool(task_mgr.mark_incomplete, user_id, cust_id)
    return {"complete": False}


@app.put("/tasks/{user_id}/{cust_id}")
async def update_task(user_id: int, cust_id: int, updates: TaskUpdate):
    # Split updates into custom-task fields and schedule fields so the right
    # manager method handles each group.
    task_fields = {}
    schedule_fields = {}
    for field, value in updates.model_dump(exclude_none=True).items():
        if field in {"cust_name", "cust_desc"}:
            task_fields[field] = value
        elif field in {"task_date", "task_stime", "task_etime"}:
            schedule_fields[field] = value

    if task_fields:
        await run_in_threadpool(task_mgr.update_task, cust_id, **task_fields)
    if schedule_fields:
        await run_in_threadpool(task_mgr.update_schedule, user_id, cust_id, **schedule_fields)
    return {"updated": True}


# ----- Predefined-task endpoints ----- #

@app.get("/catalog")
async def get_catalog():
    """Return all predefined tasks grouped by category."""
    catalog = await run_in_threadpool(task_mgr.get_predefined_tasks)
    # Convert to list format for JSON response.
    result = []
    for type_name, tasks in catalog.items():
        result.append({"type_name": type_name, "tasks": tasks})
    # Sort categories alphabetically.
    result.sort(key=lambda x: x["type_name"])
    return {"catalog": result}


@app.post("/tasks/{user_id}/assign")
async def assign_predefined_task(user_id: int, body: PredefinedAssign):
    """Assign a predefined task to a user with scheduling info."""
    await run_in_threadpool(
        task_mgr.assign_predefined,
        user_id, body.task_id, body.date, body.start_time, body.end_time
    )
    return {"assigned": True}


@app.delete("/tasks/{user_id}/unassign/{usertask_id}")
async def unassign_predefined_task(user_id: int, usertask_id: int):
    """Remove a user's assignment of a predefined task (does not delete the task itself)."""
    await run_in_threadpool(task_mgr.unassign_predefined, user_id, usertask_id)
    return {"unassigned": True}


@app.put("/tasks/{user_id}/predefined/{usertask_id}")
async def update_predefined_schedule(user_id: int, usertask_id: int, updates: PredefinedUpdate):
    """Update the schedule of an assigned predefined task."""
    schedule_fields = {}
    for field, value in updates.model_dump(exclude_none=True).items():
        if field in {"task_date", "task_stime", "task_etime"}:
            schedule_fields[field] = value
    if schedule_fields:
        # For predefined tasks, the composite key is (user_id, task_id) where task_id = usertask_id.
        await run_in_threadpool(task_mgr.update_schedule, user_id, usertask_id, **schedule_fields)
    return {"updated": True}


@app.put("/tasks/{user_id}/predefined/{usertask_id}/complete")
async def complete_predefined_task(user_id: int, usertask_id: int):
    await run_in_threadpool(task_mgr.mark_complete, user_id, usertask_id)
    return {"complete": True}


@app.put("/tasks/{user_id}/predefined/{usertask_id}/incomplete")
async def incomplete_predefined_task(user_id: int, usertask_id: int):
    await run_in_threadpool(task_mgr.mark_incomplete, user_id, usertask_id)
    return {"complete": False}


##### Metrics endpoints
class MetricUpdate(BaseModel):
    """
    Schema for updating a metric value.

    Attributes:
        value (int | None): The new metric value to set. If None,
            no update will be applied.
    """
    value: int | None = None

@app.get("/metrics/{user_id}/{date}")
async def get_metric_detail(user_id: int, date: str):
    """
    Retrieve all metric data for a given user on a specific date.

    Args:
        user_id (int): The ID of the user whose metrics are requested.
        date (str): The target date in YYYY-MM-DD format.

    Returns:
        list[dict]: A list of metric records for the specified user and date.
    """
    return await run_in_threadpool(metric_mgr.read_user_metrics, user_id, date)

@app.put("/metrics/{user_id}/{metric_id}")
async def update_metric(user_id: int, metric_id: int, payload: MetricUpdate):
    """
    Update the value of a specific metric for a user.

    Args:
        user_id (int): The ID of the user owning the metric.
        metric_id (int): The ID of the metric to update.
        payload (MetricUpdate): Request body containing the new metric value.

    Returns:
        None: This endpoint does not return a response body.
    """
    await run_in_threadpool(metric_mgr.update_metric_value, user_id, metric_id, payload.value)


##### Challenges & Rewards endpoints
@app.get("/rewards")
async def get_rewards():
    rewards = await run_in_threadpool(reward_mgr.get_all_rewards)
    result = []
    for reward in rewards:
        result.append({
            "reward_id": reward.reward_id,
            "chall_id": reward.chall_id_id,
            "reward_name": reward.reward_name,
            "reward_type": reward.reward_type_id,
        })
    return result


@app.post("/rewards/user/{user_id}/claim")
async def claim_reward(user_id: int, claim: RewardClaim):
    try:
        claimed = await run_in_threadpool(
            reward_mgr.claim_reward,
            user_id,
            claim.reward_id,
            claim.status,
        )
        return {"claimed": claimed, "reward_id": claim.reward_id}
    except ValueError as err:
        raise HTTPException(status_code=400, detail=str(err))
    except Exception as err:
        raise HTTPException(status_code=500, detail="something went wrong, please try again")


@app.get("/challenges/{user_id}")
async def get_user_challenges(user_id: int):
    rows = await run_in_threadpool(
        lambda: list(
            UserChallenges
            .select(UserChallenges, Challenges)
            .join(Challenges)
            .where(UserChallenges.user_id == user_id)
        )
    )
    result = []
    for row in rows:
        result.append({
            "chall_id": row.chall_id.chall_id,
            "chall_name": row.chall_id.chall_name,
            "chall_desc": row.chall_id.chall_desc,
            "chall_sdate": str(row.chall_sdate),
            "chall_edate": str(row.chall_edate),
        })
    return result


##### Social endpoints
class FriendRequest(BaseModel):
    user_id: int
    username_or_id: int | str

@app.get("/friends/{user_id}")
async def get_user_friends(user_id: int):
    return await run_in_threadpool(social_mgr.view_friends, user_id)

@app.post("/friends/add")
async def add_friend(payload: FriendRequest):
    return await run_in_threadpool(social_mgr.add_friend, payload.user_id, payload.username_or_id)

@app.delete("/friends/remove/{user_id}/{friend_id}")
async def remove_friend(user_id: int, friend_id: int):
    return await run_in_threadpool(social_mgr.remove_friend, user_id, friend_id)
