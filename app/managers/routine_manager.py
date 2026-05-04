import asyncio

from database_manager import DatabaseManager
from database_models import Users


dbm = DatabaseManager()

class RoutineManager:
    def __init__(self, rout_name,rout_desc,rout_freq):
        self.rout_name = rout_name
        self.rout_desc = rout_desc
        self.rout_freq = rout_freq

    async def createRoutine(self):
        routine = await dbm.run(lambda: dbm.create_record(
            dbm.models["Routines"],
            rout_name=self.rout_name,
            rout_desc=self.rout_desc,
            rout_freq=self.rout_freq
        ))
    
    async def readRoutine(self, value):
        routine = await dbm.run(lambda: dbm.read_record(dbm.models["Routines"], value))
        if routine is None:
            print("This Routine Doesn't Exist")
            return None
        else:
            print("Fetched Routine:", routine.rout_name, routine.rout_freq)
    
    async def deleteRoutine(self, value):
        routine = await dbm.run(lambda: dbm.delete_record(dbm.models["Routines"], value))
        if routine is None:
            print("This Routine Doesn't Exist")
            return None
        else:
            print("Deleted Routine:", routine.rout_name, routine.rout_freq)
    
    async def readAllRoutines(self):
        routines = await dbm.run(lambda: list(dbm.models["Routines"].select()))
        if not routines:
            print("No routines found")
            return []
        for r in routines:
            print(r.rout_id, r.rout_name,r.rout_desc, r.rout_freq)
        return routines
    
    async def updateRoutineName(self, value, rout_name):
        routine = await dbm.run(lambda: dbm.update_record(dbm.models["Routines"], value, rout_name=rout_name))
        if routine is None:
            print("This Routine Doesn't Exist")
            return None
        else:
            print("Updated Routine Name to:", rout_name)
    
    async def updateRoutineDesc(self, value, rout_desc):
        routine = await dbm.run(lambda: dbm.update_record(dbm.models["Routines"], value, rout_desc=rout_desc))
        if routine is None:
            print("This Routine Doesn't Exist")
            return None
        else:
            print("Updated Routine Description to:", rout_desc)

    async def updateRoutineFrequency(self, value, rout_freq):
        routine = await dbm.run(lambda: dbm.update_record(dbm.models["Routines"], value, rout_freq=rout_freq))
        if routine is None:
            print("This Routine Doesn't Exist")
            return None
        else:
            print("Updated Routine Frequency to:", rout_freq)
    
    async def addRoutine(self, user_id, rout_id):
        user = await dbm.run(lambda: dbm.read_record(dbm.models["Users"], user_id))
        routine = await dbm.run(lambda: dbm.read_record(dbm.models["Routines"], rout_id))
        if user is None:
            print("This User Doesn't Exist")
            return
        if routine is None:
            print("This Routine Doesn't Exist")
            return
        await dbm.run(lambda: dbm.create_record(
            dbm.models["UserRoutines"],
            user_id=user_id,
            rout_id=rout_id
        ))

if __name__ == "__main__":
    routine_manager = RoutineManager("Morning Routine", "Daily",1)
    asyncio.run(routine_manager.readAllRoutines())

