import asyncio
from app.db.database_manager import DatabaseManager
from datetime import *

dbm = DatabaseManager()


class CompetitionManager:
    """Manages creation, retrieval, updating, and deletion of competitions.

    Attributes:
        compname (str): Name of the competition.
        comp_sdate (date): Start date of the competition.
        comp_edate (date): End date of the competition.
    """

    def __init__(self, compname, comp_sdate, comp_edate):
        """Initializes a CompetitionManager instance.

        Args:
            compname (str): Competition name.
            comp_sdate (date): Start date.
            comp_edate (date): End date.
        """
        self.compname = compname
        self.comp_sdate = comp_sdate
        self.comp_edate = comp_edate

    async def createCompetition(self):
        """Creates a new competition record in the database.

        Returns:
            None
        """
        await dbm.run(lambda: dbm.create_record(
            dbm.models["Competitions"],
            comp_name=self.compname,
            comp_sdate=self.comp_sdate,
            comp_edate=self.comp_edate
        ))

    async def printCompetition(self, value):
        """Prints a single competition's details.

        Args:
            value (Any): Primary key or lookup value for the competition.

        Returns:
            None
        """
        competition = await dbm.run(lambda: dbm.read_record(dbm.models["Competitions"], value))
        if competition is None:
            print("This Competition Doesn't Exist")
            return
        print("Fetched Competition:", competition.comp_name)

    async def readAllCompetitions(self):
        """Reads and prints all competitions from the database.

        Returns:
            list: List of all competition records.
        """
        competitions = await dbm.run(lambda: list(dbm.models["Competitions"].select()))
        if not competitions:
            print("No competitions found")
            return []

        for c in competitions:
            print(c.comp_id, c.comp_name, c.comp_sdate, c.comp_edate)

        return competitions

    async def updateCompetitionName(self, value, compname):
        """Updates the name of a competition.

        Args:
            value (Any): Competition ID.
            compname (str): New competition name.

        Returns:
            None
        """
        competition = await dbm.run(lambda: dbm.update_record(
            dbm.models["Competitions"], value, comp_name=compname
        ))
        if competition is None:
            print("This Competition Doesn't Exist")
            return
        print("Updated Competition")

    async def updateCompetitionStartDate(self, value, comp_sdate):
        """Updates the start date of a competition.

        Args:
            value (Any): Competition ID.
            comp_sdate (date): New start date.

        Returns:
            None
        """
        competition = await dbm.run(lambda: dbm.update_record(
            dbm.models["Competitions"], value, comp_sdate=comp_sdate
        ))
        if competition is None:
            print("This Competition Doesn't Exist")
            return
        print("Updated Competition")

    async def updateCompetitionEndDate(self, value, comp_edate):
        """Updates the end date of a competition.

        Args:
            value (Any): Competition ID.
            comp_edate (date): New end date.

        Returns:
            None
        """
        competition = await dbm.run(lambda: dbm.update_record(
            dbm.models["Competitions"], value, comp_edate=comp_edate
        ))
        if competition is None:
            print("This Competition Doesn't Exist")
            return
        print("Updated Competition")

    async def deleteCompetition(self, value):
        """Deletes a competition from the database.

        Args:
            value (Any): Competition ID.

        Returns:
            None
        """
        comp = await dbm.run(lambda: dbm.delete_record(dbm.models["Competitions"], value))
        if comp is None:
            print("This Competition Doesn't Exist")
            return
        print("Deleted Competition")

    def addToCompetition(self):
        """Placeholder for adding participants or items to a competition.

        Returns:
            None
        """
        pass


if __name__ == "__main__":
    comp_manager = CompetitionManager("Test Competition2", date(2026, 6, 1), date(2026, 12, 1))
    asyncio.run(comp_manager.readAllCompetitions())
    print("---------------------------------------")
    asyncio.run(comp_manager.updateCompetitionName(7, "Updated Test Competition1"))
    asyncio.run(comp_manager.readAllCompetitions())