from app.db.database_models import CustomTasks, Tasks, TaskType, UserTask


class TaskManager:
    def __init__(self, db=None):
        # Database manager gets passed in from managers.py so we share one instance.
        self._db = db

    def add_task(self, user, name, description=None):
        """Create a custom task in the customTask table (no assignment)."""
        if not name or not name.strip():
            raise ValueError("Task name cannot be empty")

        custom_task = self._db.create_record(
            CustomTasks, cust_name=name, cust_desc=description
        )
        return custom_task

    def assign_custom(self, user_id, cust_id, date, start_time, end_time):
        """Assign an existing custom task to a user with scheduling info."""
        self._db.create_record(
            UserTask,
            user_id=user_id,
            task_id=None,
            cust_id=cust_id,
            task_complete=False,
            task_date=date,
            task_stime=start_time,
            task_etime=end_time,
        )

    def remove_task(self, user_id, cust_id):
        # Remove the user-task link first, then the custom task itself.
        # This order matters because UserTask has a foreign key to CustomTasks.
        self._db.delete_record(UserTask, (user_id, cust_id))
        self._db.delete_record(CustomTasks, cust_id)

    def get_tasks(self, user_id):
        """
        Pull all tasks (both predefined and custom) for a user.
        Each returned dict has a 'task_type' field: 'predefined' or 'custom'.
        """
        result = []

        # --- Predefined tasks: join UserTask (where task_id is set) with Tasks ---
        predefined_query = (
            UserTask
            .select(UserTask, Tasks, TaskType)
            .join(Tasks, on=(UserTask.task_id == Tasks.task_id))
            .join(TaskType, on=(Tasks.type_id == TaskType.type_id))
            .where(UserTask.user_id == user_id)
            .where(UserTask.task_id.is_null(False))
        )
        for entry in predefined_query:
            result.append({
                "task_type": "predefined",
                # CompositeKey is (user_id, task_id) — use task_id as the usertask_id
                "usertask_id": entry.task_id.task_id,
                "task_id": entry.task_id.task_id,
                "cust_id": None,
                "name": entry.task_id.task_name,
                "description": entry.task_id.task_desc,
                "type_id": entry.task_id.type_id.type_id,
                "type_name": entry.task_id.type_id.type_name,
                "task_complete": entry.task_complete,
                "task_date": str(entry.task_date),
                "task_stime": str(entry.task_stime),
                "task_etime": str(entry.task_etime),
            })

        # --- Custom tasks: join UserTask (where cust_id is set) with CustomTasks ---
        custom_query = (
            UserTask
            .select(UserTask, CustomTasks)
            .join(CustomTasks, on=(UserTask.cust_id == CustomTasks.cust_id))
            .where(UserTask.user_id == user_id)
            .where(UserTask.cust_id.is_null(False))
        )
        for entry in custom_query:
            result.append({
                "task_type": "custom",
                "usertask_id": entry.cust_id.cust_id,
                "task_id": None,
                "cust_id": entry.cust_id.cust_id,
                "name": entry.cust_id.cust_name,
                "description": entry.cust_id.cust_desc,
                "type_id": entry.cust_id.type_id.type_id,
                "type_name": "Custom",
                "task_complete": entry.task_complete,
                "task_date": str(entry.task_date),
                "task_stime": str(entry.task_stime),
                "task_etime": str(entry.task_etime),
            })

        return result

    def show_tasks(self, user_id):
        # Readable output for terminal use until the UI is ready.
        tasks = self.get_tasks(user_id)
        if not tasks:
            print("No tasks found.")
            return

        for entry in tasks:
            status = "Done" if entry["task_complete"] else "Pending"
            label = entry["type_name"] if entry["task_type"] == "predefined" else "Custom"
            print(f"[{label}] {entry['name']}: {entry['description'] or 'No description'} | {entry['task_date']} {entry['task_stime']}-{entry['task_etime']} | {status}")

    def mark_complete(self, user_id, cust_id):
        self._db.update_record(UserTask, (user_id, cust_id), task_complete=True)

    def mark_incomplete(self, user_id, cust_id):
        self._db.update_record(UserTask, (user_id, cust_id), task_complete=False)

    def update_task(self, cust_id, **fields):
        # Update the custom task's own fields (name, description).
        allowed = {"cust_name", "cust_desc"}
        task_fields = {field: value for field, value in fields.items() if field in allowed}
        if task_fields:
            self._db.update_record(CustomTasks, cust_id, **task_fields)

    def update_schedule(self, user_id, cust_id, **fields):
        # Update the scheduling fields (date, start time, end time) on a user's task.
        allowed = {"task_date", "task_stime", "task_etime"}
        schedule_fields = {field: value for field, value in fields.items() if field in allowed}
        if schedule_fields:
            self._db.update_record(UserTask, (user_id, cust_id), **schedule_fields)

    #----- Predefined-task methods (read-only catalog) -----#

    def get_predefined_tasks(self):
        """Return all predefined tasks grouped by category (type_name)."""
        query = (
            Tasks
            .select(Tasks, TaskType)
            .join(TaskType, on=(Tasks.type_id == TaskType.type_id))
            .order_by(TaskType.type_name, Tasks.task_name)
        )
        # Group by category name.
        grouped = {}
        for task in query:
            cat_name = task.type_id.type_name
            if cat_name not in grouped:
                grouped[cat_name] = []
            grouped[cat_name].append({
                "task_id": task.task_id,
                "task_name": task.task_name,
                "task_desc": task.task_desc,
                "type_id": task.type_id.type_id,
                "type_name": cat_name,
            })
        return grouped

    def get_predefined_by_category(self, type_id):
        """Return predefined tasks filtered by category."""
        query = (
            Tasks
            .select(Tasks, TaskType)
            .join(TaskType, on=(Tasks.type_id == TaskType.type_id))
            .where(Tasks.type_id == type_id)
            .order_by(Tasks.task_name)
        )
        result = []
        for task in query:
            result.append({
                "task_id": task.task_id,
                "task_name": task.task_name,
                "task_desc": task.task_desc,
                "type_id": task.type_id.type_id,
                "type_name": task.type_id.type_name,
            })
        return result

    def assign_predefined(self, user_id, task_id, date, start_time, end_time):
        """Assign a predefined task to a user with scheduling info."""
        self._db.create_record(
            UserTask,
            user_id=user_id,
            task_id=task_id,
            cust_id=None,
            task_complete=False,
            task_date=date,
            task_stime=start_time,
            task_etime=end_time,
        )

    def unassign_predefined(self, user_id, task_id):
        """Remove a user's assignment of a predefined task (does NOT delete the task itself)."""
        # The primary key for UserTask is (user_id, task_id).
        self._db.delete_record(UserTask, (user_id, task_id))
