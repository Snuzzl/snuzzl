from fastapi import FastAPI
from contextlib import asynccontextmanager
from fastapi.concurrency import run_in_threadpool
from pydantic import BaseModel
from database_connection import db
from database_manager import DatabaseManager
from task_manager import TaskManager

# Shared instances so the server and task manager use one DB connection.
db_manager = DatabaseManager()
task_mgr = TaskManager(db=db_manager)


@asynccontextmanager
async def lifespan(app: FastAPI):
    db.connect()
    print("Database connected.")
    yield
    db.close()
    print("Database closed.")


app = FastAPI(lifespan=lifespan)


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
