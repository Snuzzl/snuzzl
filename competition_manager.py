import asyncio

from database_manager import DatabaseManager
from database_models import Users

from datetime import *

dbm = DatabaseManager()

class CompetitionManager:
    def __init__(self, compname, comp_sdate, comp_edate):
        self.compname = compname
        self.comp_sdate = comp_sdate
        self.comp_edate = comp_edate

    async def createCompetition(self):
        competition = await dbm.run(lambda: dbm.create_record(
        dbm.models["Competitions"],
        compname = self.compname,
        comp_sdate = self.comp_sdate,
        comp_edate = self.comp_edate
    ))

    def updateCompetition(self):
        pass

    def deleteCompetition(self):
        pass

    def addToCompetition(self):
        pass

if __name__ == "__main__":
    comp_manager = CompetitionManager("Test Competition", date(2026, 6, 1), date(2026, 12, 1))
    comp_manager.createCompetition()   