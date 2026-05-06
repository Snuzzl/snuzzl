from database_models import Tasks, UserTask


class TaskManager:
    def __init__(self,db=None):
        # Database manager gets passed in from managers.py so we share one instance.
        self._db = db

    def add_task(self, user, name, date, start_time, end_time, description=None):
        # Tasks need a name and a time window to complete them by.
        if not name or not name.strip():
            raise ValueError("Task name cannot be empty")
        if not date or not start_time or not end_time:
            raise ValueError("Task must have a date, start time, and end time")

        # Create the task itself first.
        task = self._db.create_record(Tasks, task_name=name, task_desc=description)

        # Then link it to the user with scheduling info.
        self._db.create_record(
            UserTask,
            user_id=user,
            task_id=task,
            task_complete=False,
            task_date=date,
            task_stime=start_time,
            task_etime=end_time,
        )
        return task

    def remove_task(self, user_id, task_id):
        # Remove the user-task link first, then the task itself.
        # This order matters because UserTask has a foreign key to Tasks.
        self._db.delete_record(UserTask, (user_id, task_id))
        self._db.delete_record(Tasks, task_id)

    def get_tasks(self, user_id):
        # Pull all tasks for a user by joining UserTask with Tasks.
        query = (
            UserTask
            .select(UserTask, Tasks)
            .join(Tasks, on=(UserTask.task_id == Tasks.task_id))
            .where(UserTask.user_id == user_id)
        )
        return list(query)

    def show_tasks(self, user_id):
        # Readable output for terminal use until the UI is ready.
        tasks = self.get_tasks(user_id)
        if not tasks:
            print("No tasks found.")
            return

        for entry in tasks:
            task = entry.task_id  # The joined Tasks object via the foreign key.
            status = "Done" if entry.task_complete else "Pending"
            date_str = str(entry.task_date) if entry.task_date else "No date"
            time_str = ""
            if entry.task_stime:
                time_str = f" {entry.task_stime}"
                if entry.task_etime:
                    time_str += f"-{entry.task_etime}"
            print(f"[{task.task_id}] {task.task_name}: {task.task_desc or 'No description'} | Date: {date_str}{time_str} | Status: {status}")

    def mark_complete(self, user_id, task_id):
        self._db.update_record(UserTask, (user_id, task_id), task_complete=True)

    def mark_incomplete(self, user_id, task_id):
        self._db.update_record(UserTask, (user_id, task_id), task_complete=False)

    def update_task(self, task_id, **fields):
        # Update the task's own fields (name, description).
        allowed = {"task_name", "task_desc"}
        task_fields = {field: value for field, value in fields.items() if field in allowed}
        if task_fields:
            self._db.update_record(Tasks, task_id, **task_fields)

    def update_schedule(self, user_id, task_id, **fields):
        # Update the scheduling fields (date, start time, end time) on a user's task.
        allowed = {"task_date", "task_stime", "task_etime"}
        schedule_fields = {field: value for field, value in fields.items() if field in allowed}
        if schedule_fields:
            self._db.update_record(UserTask, (user_id, task_id), **schedule_fields)
