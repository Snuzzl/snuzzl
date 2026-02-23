class TaskManager:
    def __init__(self):
        self._tasks = []
    # We use property for getters, variable.setter for setters. This allows for validation when adding a task, or putting custom logic in the getter before returning something.
    @property
    def tasks(self):
        return self._tasks
    def add_task(self, task):
        # If the task object we get isn't the same as Task, don't accept it.
        if not isinstance(task, Task):
            raise TypeError("Expected a task object")
        self._tasks.append(task)

    def remove_task(self, index):
        # Don't take an index outside the actual length of the tasks array or below 0. -1 wraps around to the end of the list.
        if index < 0 or index >=len(self._tasks):
            raise IndexError("Task index out of range")
        self._tasks.pop(index)

    def show_tasks(self):
        # Nicer than just looking at self.tasks in a terminal, we can use this until we get the UI.
        for index, task in enumerate(self._tasks):
            # 1 liners are good for little value updates like these.
            status = "Done" if task.completed else "Pending"
            overdue = " [OVERDUE]" if task.is_overdue() else ""
            due_str = task.due_date.strftime("%Y-%m-%d %H:%M") if task.due_date else "No due date"
            print(f"[{index}] {task.name}: {task.description} | Due: {due_str} | Status: {status}{overdue}")

class Task:
    def __init__(self):
        self._name = ""
        self._description = ""
        self._due_date = None
        self._completed = False

    @property
    def name(self):
        return self._name

    @property
    def description(self):
        return self._description

    @property
    def due_date(self):
        return self._due_date

    @property
    def completed(self):
        return self._completed

    @name.setter
    def name(self, new_name):
        # Tasks must have a name.
        if not new_name or not new_name.strip():
            raise ValueError("Task name cannot be empty")
        self._name = new_name

    @description.setter
    def description(self, new_description):
        self._description = new_description

    @due_date.setter
    def due_date(self, new_due_date):
        self._due_date = new_due_date

    @completed.setter
    def completed(self, new_completed):
        self._completed = new_completed

    def is_overdue(self):
        # If no due date set or already completed, not overdue.
        if self._due_date is None or self._completed:
            return False
        from datetime import datetime
        # This evaluates to true if the current time is past the set due date.
        return datetime.now() > self._due_date

    def mark_complete(self):
        self._completed = True

    def mark_incomplete(self):
        self._completed = False
