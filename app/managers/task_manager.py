from app.db.database_models import CustomTasks, Tasks, TaskType, UserTask


class TaskManager:
    """Manages predefined tasks, custom tasks, and user task assignments."""

    def __init__(self, db=None):
        """Initializes the TaskManager.

        Args:
            db: Database manager instance used for CRUD operations.
        """
        self._db = db

    def add_task(self, user, name, description=None):
        """Creates a custom task (not yet assigned to a user).

        Args:
            user (Any): Unused placeholder for future expansion.
            name (str): Name of the custom task.
            description (str | None): Optional task description.

        Raises:
            ValueError: If the task name is empty.

        Returns:
            CustomTasks: The created custom task record.
        """
        if not name or not name.strip():
            raise ValueError("Task name cannot be empty")

        return self._db.create_record(
            CustomTasks,
            cust_name=name,
            cust_desc=description
        )

    def assign_custom(self, user_id, cust_id, date, start_time, end_time):
        """Assigns an existing custom task to a user with scheduling details.

        Args:
            user_id (int): User ID.
            cust_id (int): Custom task ID.
            date (date): Scheduled date.
            start_time (time): Start time.
            end_time (time): End time.

        Returns:
            None
        """
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
        """Removes a custom task and its user assignment.

        Args:
            user_id (int): User ID.
            cust_id (int): Custom task ID.

        Returns:
            None
        """
        self._db.delete_record(UserTask, (user_id, cust_id))
        self._db.delete_record(CustomTasks, cust_id)

    def get_tasks(self, user_id):
        """Retrieves all tasks (predefined and custom) assigned to a user.

        Args:
            user_id (int): User ID.

        Returns:
            list[dict]: List of task dictionaries containing:
                - task_type
                - usertask_id
                - task_id / cust_id
                - name
                - description
                - type_id
                - type_name
                - task_complete
                - task_date
                - task_stime
                - task_etime
        """
        result = []

        # Predefined tasks
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

        # Custom tasks
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
        """Prints a readable list of tasks for terminal debugging.

        Args:
            user_id (int): User ID.

        Returns:
            None
        """
        tasks = self.get_tasks(user_id)
        if not tasks:
            print("No tasks found.")
            return

        for entry in tasks:
            status = "Done" if entry["task_complete"] else "Pending"
            label = entry["type_name"] if entry["task_type"] == "predefined" else "Custom"
            print(
                f"[{label}] {entry['name']}: {entry['description'] or 'No description'} | "
                f"{entry['task_date']} {entry['task_stime']}-{entry['task_etime']} | {status}"
            )

    def mark_complete(self, user_id, cust_id):
        """Marks a custom task as complete.

        Args:
            user_id (int): User ID.
            cust_id (int): Custom task ID.

        Returns:
            None
        """
        self._db.update_record(UserTask, (user_id, cust_id), task_complete=True)

    def mark_incomplete(self, user_id, cust_id):
        """Marks a custom task as incomplete.

        Args:
            user_id (int): User ID.
            cust_id (int): Custom task ID.

        Returns:
            None
        """
        self._db.update_record(UserTask, (user_id, cust_id), task_complete=False)

    def update_task(self, cust_id, **fields):
        """Updates fields of a custom task.

        Args:
            cust_id (int): Custom task ID.
            **fields: Allowed fields include:
                - cust_name
                - cust_desc

        Returns:
            None
        """
        allowed = {"cust_name", "cust_desc"}
        task_fields = {field: value for field, value in fields.items() if field in allowed}
        if task_fields:
            self._db.update_record(CustomTasks, cust_id, **task_fields)

    def update_schedule(self, user_id, cust_id, **fields):
        """Updates scheduling details for a user's task.

        Args:
            user_id (int): User ID.
            cust_id (int): Custom task ID.
            **fields: Allowed fields include:
                - task_date
                - task_stime
                - task_etime

        Returns:
            None
        """
        allowed = {"task_date", "task_stime", "task_etime"}
        schedule_fields = {field: value for field, value in fields.items() if field in allowed}
        if schedule_fields:
            self._db.update_record(UserTask, (user_id, cust_id), **schedule_fields)

    def get_predefined_tasks(self):
        """Returns all predefined tasks grouped by category.

        Returns:
            dict[str, list[dict]]: Mapping of category name → list of tasks.
        """
        query = (
            Tasks
            .select(Tasks, TaskType)
            .join(TaskType, on=(Tasks.type_id == TaskType.type_id))
            .order_by(TaskType.type_name, Tasks.task_name)
        )

        grouped = {}
        for task in query:
            cat_name = task.type_id.type_name
            grouped.setdefault(cat_name, []).append({
                "task_id": task.task_id,
                "task_name": task.task_name,
                "task_desc": task.task_desc,
                "type_id": task.type_id.type_id,
                "type_name": cat_name,
            })

        return grouped

    def get_predefined_by_category(self, type_id):
        """Returns predefined tasks filtered by category.

        Args:
            type_id (int): Task type/category ID.

        Returns:
            list[dict]: List of predefined tasks in the category.
        """
        query = (
            Tasks
            .select(Tasks, TaskType)
            .join(TaskType, on=(Tasks.type_id == TaskType.type_id))
            .where(Tasks.type_id == type_id)
            .order_by(Tasks.task_name)
        )

        return [
            {
                "task_id": task.task_id,
                "task_name": task.task_name,
                "task_desc": task.task_desc,
                "type_id": task.type_id.type_id,
                "type_name": task.type_id.type_name,
            }
            for task in query
        ]

    def assign_predefined(self, user_id, task_id, date, start_time, end_time):
        """Assigns a predefined task to a user.

        Args:
            user_id (int): User ID.
            task_id (int): Predefined task ID.
            date (date): Scheduled date.
            start_time (time): Start time.
            end_time (time): End time.

        Returns:
            None
        """
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
        """Removes a predefined task assignment from a user.

        Args:
            user_id (int): User ID.
            task_id (int): Predefined task ID.

        Returns:
            None
        """
        self._db.delete_record(UserTask, (user_id, task_id))