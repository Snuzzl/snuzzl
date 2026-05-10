import asyncio
from concurrent.futures import ThreadPoolExecutor
from peewee import *
from app.db.database_models import *

executor = ThreadPoolExecutor(max_workers=10)

class DatabaseManager:

    def __init__(self):
        self.models = dbmodel_list

    async def run(self, func):
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(executor, func)

    #----- CREATE -----#

    def create_record(self, table, **data):
        return table.create(**data)

    #----- READ -----#

    def read_record(self, table, *pk_values):
        pk = table._meta.primary_key
        try:
            if isinstance(pk, CompositeKey):
                return table.get(pk == tuple(pk_values))
            return table.get(pk == pk_values[0])
        except table.DoesNotExist:
            return None

    #----- UPDATE -----#

    def update_record(self, table, pk_values, **data):
        pk = table._meta.primary_key

        if isinstance(pk_values, (list, tuple)):
            pk_values = tuple(pk_values)
        else:
            pk_values = (pk_values,)

        if isinstance(pk, CompositeKey):
            where_clause = pk == pk_values
        else:
            where_clause = pk == pk_values[0]

        return table.update(**data).where(where_clause).execute()

    #----- DELETE -----#

    def delete_record(self, table, pk_values):
        pk = table._meta.primary_key

        if isinstance(pk_values, (list, tuple)):
            pk_values = tuple(pk_values)
        else:
            pk_values = (pk_values,)

        if isinstance(pk, CompositeKey):
            where_clause = pk == pk_values
        else:
            where_clause = pk == pk_values[0]

        return table.delete().where(where_clause).execute()

