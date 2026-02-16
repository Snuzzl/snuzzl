class TaskManager:
    def __init__(self):
        self._tasks = []
    
    @property
    def tasks(self):
        return self._tasks
    def add_task(self, task):
        self._tasks.append(task)

    def remove_task(self, index):
        if index < len(self._tasks):
            self._tasks.pop(index)

    def show_tasks(self):
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
        self._name = newName
    @description.setter
    def description(self,newDescription):
        self._description = newDescription
    @due.setter
    def due(self,newDue):
        self._due = newDue
