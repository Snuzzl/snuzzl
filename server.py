from fastapi import FastAPI, HTTPException
from contextlib import asynccontextmanager
from fastapi.concurrency import run_in_threadpool
from pydantic import BaseModel
from database_connection import db
from database_manager import DatabaseManager
from task_manager import TaskManager
from metric_manager import MetricManager
from reward_manager import RewardManager
from database_models import UserChallenges, Challenges
from social_manager import SocialManager

# Shared instances so the server and task manager use one DB connection.
db_manager = DatabaseManager()
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


# Request body schemas for endpoints that need structured input.
class TaskCreate(BaseModel):
    name: str
    description: str | None = None
    date: str
    start_time: str
    end_time: str


class TaskUpdate(BaseModel):
    task_name: str | None = None
    task_desc: str | None = None
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
    result = []
    for entry in tasks:
        task = entry.task_id  # The joined Tasks object via the FK.
        result.append({
            "task_id": task.task_id,
            "task_name": task.task_name,
            "task_desc": task.task_desc,
            "task_complete": entry.task_complete,
            "task_date": str(entry.task_date),
            "task_stime": str(entry.task_stime),
            "task_etime": str(entry.task_etime),
        })
    return {"tasks": result}


@app.post("/tasks/{user_id}")
async def add_task(user_id: int, task: TaskCreate):
    new_task = await run_in_threadpool(
        task_mgr.add_task, user_id, task.name, task.date,
        task.start_time, task.end_time, task.description
    )
    return {"task_id": new_task.task_id}


@app.delete("/tasks/{user_id}/{task_id}")
async def delete_task(user_id: int, task_id: int):
    await run_in_threadpool(task_mgr.remove_task, user_id, task_id)
    return {"deleted": True}


@app.put("/tasks/{user_id}/{task_id}/complete")
async def complete_task(user_id: int, task_id: int):
    await run_in_threadpool(task_mgr.mark_complete, user_id, task_id)
    return {"complete": True}


@app.put("/tasks/{user_id}/{task_id}/incomplete")
async def incomplete_task(user_id: int, task_id: int):
    await run_in_threadpool(task_mgr.mark_incomplete, user_id, task_id)
    return {"complete": False}


@app.put("/tasks/{user_id}/{task_id}")
async def update_task(user_id: int, task_id: int, updates: TaskUpdate):
    # Split updates into task fields and schedule fields so the right
    # manager method handles each group.
    task_fields = {}
    schedule_fields = {}
    for field, value in updates.model_dump(exclude_none=True).items():
        if field in {"task_name", "task_desc"}:
            task_fields[field] = value
        elif field in {"task_date", "task_stime", "task_etime"}:
            schedule_fields[field] = value

    if task_fields:
        await run_in_threadpool(task_mgr.update_task, task_id, **task_fields)
    if schedule_fields:
        await run_in_threadpool(task_mgr.update_schedule, user_id, task_id, **schedule_fields)
    return {"updated": True}


##### Metrics endpoints
class MetricUpdate(BaseModel):
    value: int | None = None


@app.get("/metrics/{user_id}/{date}")
async def get_metric_detail(user_id: int, date: str):
    return await run_in_threadpool(metric_mgr.read_user_metrics, user_id, date)



@app.put("/metrics/{user_id}/{metric_id}")
async def update_metric(user_id: int, metric_id: int, payload: MetricUpdate):
    await run_in_threadpool(metric_mgr.update_metric_value, user_id, metric_id, payload.value)


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
@app.get("/friends/{user_id}")
async def get_user_friends(user_id: int):
    return await run_in_threadpool(social_mgr.view_friends, user_id)

@app.put("/friends/add/{user_id}/{username_or_id}")
async def add_friend(user_id: int, username_or_id: int):
    return await run_in_threadpool(social_mgr.add_friend, user_id, username_or_id)

@app.put("/friends/remove/{user_id}/{friend_id}")
async def remove_friend(user_id: int, friend_id: int):
    return await run_in_threadpool(social_mgr.remove_friend, user_id, friend_id)
