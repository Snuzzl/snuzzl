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
        for i in self._tasks:
            print(f"Name: {i.name}, Description: {i.description}")

class Task:
    def __init__(self):
        self._name = ""
        self._description = ""
        self._due = False
    @property
    def name(self):
        return self._name
    @property
    def description(self):
        return self._description
    @property
    def due(self):
        return self._due
    @name.setter
    def name(self,newName):
        # Tasks must have a name.
        if not newName or not newName.strip():
            raise ValueError("Task name cannot be empty")
        self._name = newName
    @description.setter
    def description(self,newDescription):
        self._description = newDescription
    @due.setter
    def due(self,newDue):
        self._due = newDue
