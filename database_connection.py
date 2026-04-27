from peewee import PostgresqlDatabase

db = PostgresqlDatabase(
    "snuzzl_db",
    user="teamuser",
    password="BeepTheM33p1963",
    host="destructatron.net",
    port=5432
)
