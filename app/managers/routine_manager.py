import asyncio
from app.db.database_manager import DatabaseManager

dbm = DatabaseManager()


class RoutineManager:
    """Manages creation, retrieval, updating, and assignment of routines."""

    def __init__(self, rout_name, rout_desc, rout_freq):
        """Initializes a RoutineManager instance.

        Args:
            rout_name (str): Name of the routine.
            rout_desc (str): Description of the routine.
            rout_freq (int): Frequency of the routine (e.g., times per week).
        """
        self.rout_name = rout_name
        self.rout_desc = rout_desc
        self.rout_freq = rout_freq

    async def createRoutine(self):
        """Creates a new routine in the database.

        Returns:
            None
        """
        await dbm.run(lambda: dbm.create_record(
            dbm.models["Routines"],
            rout_name=self.rout_name,
            rout_desc=self.rout_desc,
            rout_freq=self.rout_freq
        ))

    async def readRoutine(self, value):
        """Reads a single routine by ID.

        Args:
            value (int): Routine ID.

        Returns:
            None | Routines: The routine record if found.
        """
        routine = await dbm.run(lambda: dbm.read_record(dbm.models["Routines"], value))
        if routine is None:
            print("This Routine Doesn't Exist")
            return None

        print("Fetched Routine:", routine.rout_name, routine.rout_freq)
        return routine

    async def deleteRoutine(self, value):
        """Deletes a routine by ID.

        Args:
            value (int): Routine ID.

        Returns:
            None
        """
        routine = await dbm.run(lambda: dbm.delete_record(dbm.models["Routines"], value))
        if routine is None:
            print("This Routine Doesn't Exist")
            return None

        print("Deleted Routine:", routine.rout_name, routine.rout_freq)

    async def readAllRoutines(self):
        """Reads and prints all routines.

        Returns:
            list: List of all routine records.
        """
        routines = await dbm.run(lambda: list(dbm.models["Routines"].select()))
        if not routines:
            print("No routines found")
            return []

        for r in routines:
            print(r.rout_id, r.rout_name, r.rout_desc, r.rout_freq)

        return routines

    async def updateRoutineName(self, value, rout_name):
        """Updates the name of a routine.

        Args:
            value (int): Routine ID.
            rout_name (str): New routine name.

        Returns:
            None
        """
        routine = await dbm.run(lambda: dbm.update_record(
            dbm.models["Routines"], value, rout_name=rout_name
        ))
        if routine is None:
            print("This Routine Doesn't Exist")
            return None

        print("Updated Routine Name to:", rout_name)

    async def updateRoutineDesc(self, value, rout_desc):
        """Updates the description of a routine.

        Args:
            value (int): Routine ID.
            rout_desc (str): New routine description.

        Returns:
            None
        """
        routine = await dbm.run(lambda: dbm.update_record(
            dbm.models["Routines"], value, rout_desc=rout_desc
        ))
        if routine is None:
            print("This Routine Doesn't Exist")
            return None

        print("Updated Routine Description to:", rout_desc)

    async def updateRoutineFrequency(self, value, rout_freq):
        """Updates the frequency of a routine.

        Args:
            value (int): Routine ID.
            rout_freq (int): New routine frequency.

        Returns:
            None
        """
        routine = await dbm.run(lambda: dbm.update_record(
            dbm.models["Routines"], value, rout_freq=rout_freq
        ))
        if routine is None:
            print("This Routine Doesn't Exist")
            return None

        print("Updated Routine Frequency to:", rout_freq)

    async def addRoutine(self, user_id, rout_id):
        """Assigns a routine to a user.

        Args:
            user_id (int): User ID.
            rout_id (int): Routine ID.

        Returns:
            None
        """
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
    routine_manager = RoutineManager("Morning Routine", "Daily", 1)
    asyncio.run(routine_manager.readAllRoutines())