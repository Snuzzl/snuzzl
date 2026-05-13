# tests/conftest.py
import sys
from pathlib import Path
import pytest
from unittest.mock import MagicMock

# Ensure project root is on sys.path
project_root = Path(__file__).resolve().parents[1]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# --- Patch peewee.PostgresqlDatabase to a mock factory so import-time DB creation won't crash ---
try:
    import peewee
    # Factory that returns a DB-like MagicMock with common methods used at import/runtime
    def _mock_postgres_db(*args, **kwargs):
        db = MagicMock(name="PostgresqlDatabaseMock")
        # Provide methods that code might call on the DB object
        db.execute = MagicMock()
        db.connect = MagicMock()
        db.close = MagicMock()
        db.create_tables = MagicMock()
        db.get_conn = MagicMock()
        return db
    peewee.PostgresqlDatabase = _mock_postgres_db
except Exception:
    # If peewee isn't importable, ignore; tests will mock manager._db anyway
    pass

@pytest.fixture
def manager():
    # Import after peewee patch so TaskManager import doesn't try to use real psycopg2
    from app.managers.task_manager import TaskManager
    m = TaskManager()
    # Inject a mocked _db with the methods TaskManager uses
    m._db = MagicMock(name="manager_db")
    m._db.create_record = MagicMock()
    m._db.read_record = MagicMock()
    m._db.update_record = MagicMock()
    m._db.delete_record = MagicMock()
    return m
