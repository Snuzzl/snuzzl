from fastapi import FastAPI, HTTPException
from contextlib import asynccontextmanager
from fastapi.concurrency import run_in_threadpool
from pydantic import BaseModel
from app.db.database_connection import db
from app.db.database_manager import DatabaseManager
from app.db.database_models import UserChallenges, Challenges
from app.managers.task_manager import TaskManager
from app.managers.metric_manager import MetricManager
from app.managers.challenge_manager import ChallengeManager
from app.managers.reward_manager import RewardManager
from app.managers.social_manager import SocialManager
from app.managers.account_manager import AccountManager
from app.managers.noti_manager import NotificationManager

# Shared instances so the server and managers use one DB connection.
db_manager = DatabaseManager()
acc_mgr = AccountManager(db=db_manager)
task_mgr = TaskManager(db=db_manager)
metric_mgr = MetricManager(db=db_manager)
challenge_mgr = ChallengeManager(db=db_manager)
reward_mgr = RewardManager(database_manager=db_manager)
social_mgr = SocialManager(db=db_manager)
noti_mgr = NotificationManager(db=db_manager)


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
    """Schema for creating a reward.

    Attributes:
        chall_id (int): Challenge ID linked to the reward.
        reward_name (str): Display name of the reward.
        reward_type (int): Reward type/category ID.
    """

    chall_id: int
    reward_name: str
    reward_type: int


class UserRewardUpdate(BaseModel):
    """Schema for bulk user reward updates.

    Attributes:
        reward_ids (list[int] | int | None): Target reward IDs.
        reward_name (str | None): Optional new reward name.
        reward_type (int | None): Optional new reward type ID.
    """

    reward_ids: list[int] | int | None = None
    reward_name: str | None = None
    reward_type: int | None = None


class RewardClaim(BaseModel):
    """Schema for reward claim requests.

    Attributes:
        reward_id (int): Reward ID to claim.
        status (str): Reward status label.
    """

    reward_id: int
    status: str = "Incomplete"


class ChallengeJoin(BaseModel):
    """Schema for challenge enrollment requests.

    Attributes:
        chall_id (int): Challenge ID to join.
        chall_sdate (str | None): Optional challenge start date.
        chall_edate (str | None): Optional challenge end date.
    """

    chall_id: int
    chall_sdate: str | None = None
    chall_edate: str | None = None


async def _award_rewards_after_completion(user_id: int):
    """Award newly completed challenge rewards after task completion.

    Args:
        user_id (int): Active user ID.

    Returns:
        list[str]: Names of rewards awarded during this call.
    """
    before_rewards = await run_in_threadpool(reward_mgr.view_user_rewards, user_id)
    before_ids = {reward.reward_id for reward in before_rewards}

    challenge_rows = await run_in_threadpool(challenge_mgr.get_user_challenges, user_id)
    for row in challenge_rows:
        status = await run_in_threadpool(
            challenge_mgr.get_user_challenge_status,
            user_id,
            row.chall_id.chall_id,
            row.chall_edate,
        )
        if status == "completed":
            await run_in_threadpool(
                reward_mgr.award_challenge_rewards,
                user_id,
                row.chall_id.chall_id,
                "Complete",
            )

    after_rewards = await run_in_threadpool(reward_mgr.view_user_rewards, user_id)
    newly_awarded = [reward for reward in after_rewards if reward.reward_id not in before_ids]
    return [reward.reward_name for reward in newly_awarded]


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
    try:
        await run_in_threadpool(task_mgr.mark_complete, user_id, cust_id)
        rewards_awarded = await _award_rewards_after_completion(user_id)
        return {"complete": True, "rewards_awarded": rewards_awarded}
    except ValueError as err:
        raise HTTPException(status_code=404, detail=str(err))


@app.put("/tasks/{user_id}/{cust_id}/incomplete")
async def incomplete_task(user_id: int, cust_id: int):
    try:
        await run_in_threadpool(task_mgr.mark_incomplete, user_id, cust_id)
        return {"complete": False}
    except ValueError as err:
        raise HTTPException(status_code=404, detail=str(err))


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

    try:
        if task_fields:
            await run_in_threadpool(task_mgr.update_task, cust_id, **task_fields)
        if schedule_fields:
            await run_in_threadpool(task_mgr.update_schedule, user_id, cust_id, **schedule_fields)
        return {"updated": True}
    except ValueError as err:
        raise HTTPException(status_code=404, detail=str(err))


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
    try:
        if schedule_fields:
            await run_in_threadpool(task_mgr.update_schedule, user_id, usertask_id, **schedule_fields)
        return {"updated": True}
    except ValueError as err:
        raise HTTPException(status_code=404, detail=str(err))


@app.put("/tasks/{user_id}/predefined/{usertask_id}/complete")
async def complete_predefined_task(user_id: int, usertask_id: int):
    try:
        await run_in_threadpool(task_mgr.mark_complete, user_id, usertask_id)
        rewards_awarded = await _award_rewards_after_completion(user_id)
        return {"complete": True, "rewards_awarded": rewards_awarded}
    except ValueError as err:
        raise HTTPException(status_code=404, detail=str(err))


@app.put("/tasks/{user_id}/predefined/{usertask_id}/incomplete")
async def incomplete_predefined_task(user_id: int, usertask_id: int):
    try:
        await run_in_threadpool(task_mgr.mark_incomplete, user_id, usertask_id)
        return {"complete": False}
    except ValueError as err:
        raise HTTPException(status_code=404, detail=str(err))


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
async def get_rewards(user_id: int | None = None):
    """Return all rewards and whether the user has already claimed each one.

    Args:
        user_id (int | None): Optional user ID used to mark claimed rewards.

    Returns:
        list[dict]: Reward records with claim-state flags.
    """
    rewards = await run_in_threadpool(reward_mgr.get_all_rewards)
    claimed_reward_ids = set()
    if user_id is not None:
        claimed_rewards = await run_in_threadpool(reward_mgr.view_user_rewards, user_id)
        claimed_reward_ids = {r.reward_id for r in claimed_rewards}
    
    result = []
    for reward in rewards:
        result.append({
            "reward_id": reward.reward_id,
            "chall_id": reward.chall_id_id,
            "reward_name": reward.reward_name,
            "reward_type": reward.reward_type_id,
            "user_claimed": reward.reward_id in claimed_reward_ids,
        })
    return result


@app.get("/rewards/user/{user_id}")
async def get_user_claimed_rewards(user_id: int):
    """Return rewards claimed by a specific user.

    Args:
        user_id (int): User ID.

    Returns:
        list[dict]: Claimed reward records for the user.
    """
    rewards = await run_in_threadpool(reward_mgr.view_user_rewards, user_id)
    result = []
    for reward in rewards:
        result.append({
            "reward_id": reward.reward_id,
            "reward_name": reward.reward_name,
            "reward_type": reward.reward_type_id,
            "chall_id": reward.chall_id_id,
        })
    return result


@app.post("/rewards/user/{user_id}/claim")
async def claim_reward(user_id: int, claim: RewardClaim):
    """Claim challenge rewards when challenge completion requirements are met.

    Args:
        user_id (int): User ID.
        claim (RewardClaim): Claim payload containing reward ID and status.

    Returns:
        dict: Claim status, reward ID, and already-claimed indicator.

    Raises:
        HTTPException: If reward/challenge state is invalid or server errors occur.
    """
    try:
        reward = await run_in_threadpool(reward_mgr.get_reward, claim.reward_id)
        if reward is None:
            raise HTTPException(status_code=400, detail="reward_id does not exist")

        enrollment = await run_in_threadpool(
            db_manager.read_record,
            UserChallenges,
            user_id,
            reward.chall_id_id,
        )
        if enrollment is None:
            raise HTTPException(status_code=400, detail="join this challenge before claiming its reward")

        status = await run_in_threadpool(
            challenge_mgr.get_user_challenge_status,
            user_id,
            reward.chall_id_id,
            enrollment.chall_edate,
        )
        if status != "completed":
            raise HTTPException(status_code=400, detail="complete challenge requirements before claiming this reward")

        newly_awarded = await run_in_threadpool(
            reward_mgr.award_challenge_rewards,
            user_id,
            reward.chall_id_id,
            "Complete",
        )
        return {
            "claimed": True,
            "reward_id": claim.reward_id,
            "already_claimed": newly_awarded == 0,
        }
    except HTTPException:
        raise
    except ValueError as err:
        raise HTTPException(status_code=400, detail=str(err))
    except Exception as err:
        raise HTTPException(status_code=500, detail="something went wrong, please try again")


@app.get("/challenges")
async def get_challenges_catalog():
    """Return challenge catalog with required-task summaries.

    Returns:
        list[dict]: Challenge catalog records enriched with requirement metadata.
    """
    rows = await run_in_threadpool(challenge_mgr.get_all_challenges)
    result = []
    for row in rows:
        required = await run_in_threadpool(
            challenge_mgr.get_required_task_summary,
            row.chall_id,
        )
        result.append({
            "chall_id": row.chall_id,
            "chall_name": row.chall_name,
            "chall_desc": row.chall_desc,
            "required_count": required["count"],
            "required_summary": required["summary"],
            "required_by_type": required["by_type"],
            "required_task_ids": required["task_ids"],
            "requirement_kind": "tasks",
        })
    return result


@app.post("/challenges/{user_id}/join")
async def join_user_challenge(user_id: int, payload: ChallengeJoin):
    """Enroll a user in a challenge.

    Args:
        user_id (int): User ID.
        payload (ChallengeJoin): Join payload with challenge/date values.

    Returns:
        dict: Enrollment confirmation and date values.

    Raises:
        HTTPException: If input validation fails or server errors occur.
    """
    try:
        row = await run_in_threadpool(
            challenge_mgr.join_challenge,
            user_id,
            payload.chall_id,
            payload.chall_sdate,
            payload.chall_edate,
        )
        return {
            "joined": True,
            "chall_id": row.chall_id_id,
            "chall_sdate": str(row.chall_sdate),
            "chall_edate": str(row.chall_edate),
        }
    except ValueError as err:
        raise HTTPException(status_code=400, detail=str(err))
    except Exception:
        raise HTTPException(status_code=500, detail="something went wrong, please try again")


@app.delete("/challenges/{user_id}/{chall_id}")
async def leave_user_challenge(user_id: int, chall_id: int):
    """Remove user enrollment from a challenge.

    Args:
        user_id (int): User ID.
        chall_id (int): Challenge ID.

    Returns:
        dict: Leave confirmation payload.

    Raises:
        HTTPException: If unenrollment fails or server errors occur.
    """
    try:
        await run_in_threadpool(challenge_mgr.leave_challenge, user_id, chall_id)
        return {"left": True, "chall_id": chall_id}
    except ValueError as err:
        raise HTTPException(status_code=400, detail=str(err))
    except Exception:
        raise HTTPException(status_code=500, detail="something went wrong, please try again")


@app.get("/challenges/{user_id}")
async def get_user_challenges(user_id: int):
    """Return all challenges joined by a user with live progress/status data.

    Args:
        user_id (int): User ID.

    Returns:
        list[dict]: User challenge records with status and requirement progress.
    """
    rows = await run_in_threadpool(challenge_mgr.get_user_challenges, user_id)
    result = []
    for row in rows:
        status = await run_in_threadpool(
            challenge_mgr.get_user_challenge_status,
            user_id,
            row.chall_id.chall_id,
            row.chall_edate,
        )
        required = await run_in_threadpool(
            challenge_mgr.get_required_task_summary,
            row.chall_id.chall_id,
        )
        progress = await run_in_threadpool(
            challenge_mgr.get_required_task_progress,
            user_id,
            row.chall_id.chall_id,
        )
        if status == "completed":
            await run_in_threadpool(
                reward_mgr.award_challenge_rewards,
                user_id,
                row.chall_id.chall_id,
            )
        result.append({
            "chall_id": row.chall_id.chall_id,
            "chall_name": row.chall_id.chall_name,
            "chall_desc": row.chall_id.chall_desc,
            "chall_sdate": str(row.chall_sdate),
            "chall_edate": str(row.chall_edate),
            "challenge_status": status,
            "required_count": required["count"],
            "required_summary": required["summary"],
            "required_by_type": required["by_type"],
            "required_task_ids": required["task_ids"],
            "required_progress": progress,
            "requirement_kind": "tasks",
        })
    return result


@app.get("/challenges/{user_id}/{chall_id}/required-tasks")
async def get_required_challenge_tasks(user_id: int, chall_id: int):
    """Return required tasks and completion progress for a user challenge.

    Args:
        user_id (int): User ID.
        chall_id (int): Challenge ID.

    Returns:
        dict: Required task list plus summary/progress metadata.

    Raises:
        HTTPException: If challenge input is invalid or server errors occur.
    """
    try:
        tasks = await run_in_threadpool(
            challenge_mgr.get_required_tasks_for_user,
            user_id,
            chall_id,
        )
        required = await run_in_threadpool(
            challenge_mgr.get_required_task_summary,
            chall_id,
        )
        progress = await run_in_threadpool(
            challenge_mgr.get_required_task_progress,
            user_id,
            chall_id,
        )
        return {
            "chall_id": chall_id,
            "tasks": tasks,
            "required_count": required["count"],
            "required_summary": required["summary"],
            "required_by_type": required["by_type"],
            "required_progress": progress,
            "requirement_kind": "tasks",
        }
    except ValueError as err:
        raise HTTPException(status_code=400, detail=str(err))
    except Exception:
        raise HTTPException(status_code=500, detail="something went wrong, please try again")


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


##### Notification endpoints
class NotificationFriendRequest(BaseModel):
    """Schema for friend-request notification actions.

    Attributes:
        user_id (int): Acting user ID.
        friend_id (int): Related friend ID.
    """

    user_id: int
    friend_id: int

class CompInvite(BaseModel):
    user_id: int
    comp_id: int

@app.get("/notifications/friends/{user_id}")
async def get_friends(user_id: int):
    return await run_in_threadpool(noti_mgr.get_friend_requests, user_id)

@app.put("/notifications/accept_request")
async def accept_request(payload: NotificationFriendRequest):
    """Accept an incoming friend request.

    Args:
        payload (NotificationFriendRequest): User/friend request payload.

    Returns:
        Any: Manager response payload.
    """
    return await run_in_threadpool(noti_mgr.accept_request, payload.user_id, payload.friend_id)

@app.post("/notifications/deny_request")
async def deny_request(payload: NotificationFriendRequest):
    """Deny an incoming friend request.

    Args:
        payload (NotificationFriendRequest): User/friend request payload.

    Returns:
        Any: Manager response payload.
    """
    return await run_in_threadpool(noti_mgr.deny_request, payload.user_id, payload.friend_id)

@app.get("/notifications/invites/{user_id}")
async def get_invites(user_id: int):
    return await run_in_threadpool(noti_mgr.get_competition_invites, user_id)

@app.put("/notifications/accept_invite")
async def accept_invite(payload: CompInvite):
    return await run_in_threadpool(noti_mgr.accept_invite, payload.user_id, payload.comp_id)

@app.post("/notifications/deny_invite")
async def deny_invite(payload: CompInvite):
    return await run_in_threadpool(noti_mgr.deny_invite, payload.user_id, payload.comp_id)

@app.get("/notifications/deadlines/{user_id}")
async def get_deadlines(user_id: int):
    return await run_in_threadpool(noti_mgr.get_competition_deadlines, user_id)