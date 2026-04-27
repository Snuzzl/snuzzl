from fastapi import FastAPI, HTTPException
from contextlib import asynccontextmanager
from fastapi.concurrency import run_in_threadpool
from pydantic import BaseModel
from database_connection import db
from database_manager import DatabaseManager
from task_manager import TaskManager
from metric_manager import MetricManager

# Shared instances so the server and task manager use one DB connection.
db_manager = DatabaseManager()
task_mgr = TaskManager(db=db_manager)
metric_mgr = MetricManager(db=db_manager)


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
    metrics = await run_in_threadpool(metric_mgr.read_user_metrics, user_id, date)
    results = []
    for metric in metrics:
        results.append({
            "metric_id": metric.met_id.met_id,
            "metric_name": metric.met_id.met_name,
            "metric_desc": metric.met_id.met_desc,
            "metric_min": metric.met_id.met_min,
            "metric_max": metric.met_id.met_max,
            "metric_value": metric.metval_val,
            "last_updated": str(metric.metval_date)
            })
    return results


@app.put("/metrics/{user_id}/{metric_id}")
async def update_metric(user_id: int, metric_id: int, payload: MetricUpdate):
    await run_in_threadpool(metric_mgr.update_metric_value, user_id, metric_id, payload.value)