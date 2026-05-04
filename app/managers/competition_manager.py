import asyncio
from app.db.database_manager import DatabaseManager
from datetime import *

dbm = DatabaseManager()

class CompetitionManager:
    def __init__(self, compname, comp_sdate, comp_edate):
        self.compname = compname
        self.comp_sdate = comp_sdate
        self.comp_edate = comp_edate
    def __init__(self, compname, comp_sdate, comp_edate):
        self.compname = compname
        self.comp_sdate = comp_sdate
        self.comp_edate = comp_edate

    async def createCompetition(self):
        competition = await dbm.run(lambda: dbm.create_record(
        dbm.models["Competitions"],
        comp_name = self.compname,
        comp_sdate = self.comp_sdate,
        comp_edate = self.comp_edate
    ))

    async def printCompetition(self,value):
        competition = await dbm.run(lambda: dbm.read_record(dbm.models["Competitions"], value))
        if competition is None:
            print("This Competition Doesn't Exist")
            return
        print("Fetched Competition:", competition.comp_name)
    
    async def readAllCompetitions(self):
        competitions = await dbm.run(lambda: list(dbm.models["Competitions"].select()))
        if not competitions:
            print("No competitions found")
            return []
        for c in competitions:
            print(c.comp_id, c.comp_name, c.comp_sdate, c.comp_edate)
        return competitions
    
    async def updateCompetitionName(self, value, compname):
        competition = await dbm.run(lambda: dbm.update_record(dbm.models["Competitions"], value, comp_name=compname))
        if competition is None:
            print("This Competition Doesn't Exist")
            return
        print("Updated Competition")
    
    async def updateCompetitionStartDate(self, value, comp_sdate):
        competition = await dbm.run(lambda: dbm.update_record(dbm.models["Competitions"], value, comp_sdate=comp_sdate))
        if competition is None:
            print("This Competition Doesn't Exist")
            return
        print("Updated Competition")
    
    async def updateCompetitionEndDate(self, value, comp_edate):
        competition = await dbm.run(lambda: dbm.update_record(dbm.models["Competitions"], value, comp_edate=comp_edate))
        if competition is None:
            print("This Competition Doesn't Exist")
            return
        print("Updated Competition")

    async def deleteCompetition(self, value):
        comp = await dbm.run(lambda: dbm.delete_record(dbm.models["Competitions"], value))
        if comp is None:
            print("This Competition Doesn't Exist")
            return
        print("Deleted Competition")

    def addToCompetition(self):
        pass

if __name__ == "__main__":
    comp_manager = CompetitionManager("Test Competition2", date(2026, 6, 1), date(2026, 12, 1))
    #asyncio.run(comp_manager.createCompetition())
    #asyncio.run(comp_manager.printCompetition())
    asyncio.run(comp_manager.readAllCompetitions())
    #asyncio.run(comp_manager.deleteCompetition(8))
    print("---------------------------------------")
    asyncio.run(comp_manager.updateCompetitionName(7, "Updated Test Competition1"))
    asyncio.run(comp_manager.readAllCompetitions())