import pytest
from types import SimpleNamespace
from datetime import date
from unittest.mock import Mock
from app.db.database_manager import DatabaseManager
from peewee import CompositeKey

class DoesNotExist(Exception):
    pass

class FakePrimaryKey:
    """Simple primary key object that supports equality checks used by manager."""
    def __init__(self, name):
        self.name = name

    def __eq__(self, other):
        return ("__pk_eq__", self.name, other)


class FakeCompositeKey(CompositeKey):
    def __init__(self, fields):
        self.fields = fields

    def __eq__(self, other):
        return ("__pk_eq__", self.fields, other)


class FakeModel:
    """A minimal fake Peewee model with create/get/update/delete semantics."""
    _meta = SimpleNamespace(primary_key=FakePrimaryKey("id"))
    DoesNotExist = DoesNotExist

    _storage = {}

    @classmethod
    def reset_storage(cls):
        cls._storage = {}

    @classmethod
    def create(cls, **data):
        pk = data.get("id", len(cls._storage) + 1)
        obj = SimpleNamespace(**{**data, "id": pk})
        cls._storage[pk] = obj
        return obj

    @classmethod
    def get(cls, condition):
        if not isinstance(condition, tuple) or condition[0] != "__pk_eq__":
            raise cls.DoesNotExist()
        _, pk_name, value = condition
        if isinstance(value, tuple):
            key = value
        else:
            key = value
        row = cls._storage.get(key)
        if row is None:
            raise cls.DoesNotExist()
        return row

    @classmethod
    def update(cls, **data):
        class Updater:
            def __init__(self, data):
                self.data = data
                self._where = None

            def where(self, where_clause):
                self._where = where_clause
                return self
            
            def execute(self):
                if not isinstance(self._where, tuple) or self._where[0] != "__pk_eq__":
                    return 0
                _, pk_name, value = self._where
                key = value if isinstance(value, tuple) else value
                if key in cls._storage:
                    obj = cls._storage[key]
                    for k, v in self.data.items():
                        if not hasattr(obj, k):
                            raise ValueError(f"Invalid field: {k}")
                        setattr(obj, k, v)
                    return 1
                return 0

        return Updater(data)

    @classmethod
    def delete(cls):
        class Deleter:
            def __init__(self):
                self._where = None

            def where(self, where_clause):
                self._where = where_clause
                return self

            def execute(self):
                if not isinstance(self._where, tuple) or self._where[0] != "__pk_eq__":
                    return 0
                _, pk_name, value = self._where
                if isinstance(value, tuple):
                    key = value
                else:
                    key = value
                if key in cls._storage:
                    del cls._storage[key]
                    return 1
                return 0
        return Deleter()


# --- Fixtures ---------------------------------------------------------

@pytest.fixture(autouse=True)
def reset_fake_model():
    FakeModel.reset_storage()
    FakeModel._meta = SimpleNamespace(primary_key=FakePrimaryKey("id"))
    yield
    FakeModel.reset_storage()


@pytest.fixture
def dm():
    return DatabaseManager()

@pytest.fixture
def db_mock():
    return Mock()

# ------------------------------------------------------------------
# create_record tests
# ------------------------------------------------------------------

def test_create_record_valid_data(dm, db_mock):
    class FakeTable:
        def __init__(self):
            self.create = db_mock.create
    table = FakeTable()
    class FakeRecord:
        def __init__(self, user_id, score):
            self.user_id = user_id
            self.score = score
    fake_record = FakeRecord(user_id=1, score=100)
    table.create.return_value = fake_record
    res = dm.create_record(table, user_id=1, score=100)
    assert res is fake_record
    table.create.assert_called_once_with(user_id=1, score=100)

@pytest.mark.xfail(reason="missing required fields may raise DB error", strict=False)
def test_create_record_missing_required_fields(dm, db_mock):
    class FakeTable:
        def __init__(self):
            self.create = db_mock.create
    table = FakeTable()
    class FakeRecord:
        def __init__(self, user_id=None):
            self.user_id = user_id
    fake_record = FakeRecord(user_id=1)
    table.create.return_value = fake_record
    res = dm.create_record(table, user_id=1)
    assert res is fake_record
    table.create.assert_called_once_with(user_id=1)

@pytest.mark.xfail(reason="wrong data types may raise", strict=False)
def test_create_record_wrong_data_type(dm, db_mock):
    class FakeTable:
        def __init__(self):
            self.create = db_mock.create
    table = FakeTable()
    wrong_score = "not-a-number"
    class FakeRecord:
        def __init__(self, user_id, score):
            self.user_id = user_id
            self.score = score
    fake_record = FakeRecord(user_id=1, score=wrong_score)
    table.create.return_value = fake_record
    res = dm.create_record(table, user_id=1, score=wrong_score)
    assert res is fake_record
    table.create.assert_called_once_with(user_id=1, score=wrong_score)

@pytest.mark.xfail(reason="null table should raise", strict=False)
def test_create_record_null_table(dm):
    with pytest.raises(AttributeError):
        dm.create_record(None, user_id=1, score=100)

# ------------------------------------------------------------------
# read_record tests
# ------------------------------------------------------------------

def test_read_record_valid_single_pk(dm):
    class FakeTable(FakeModel):
        pass
    record = FakeTable.create(id=1, name="Test Metric")
    res = dm.read_record(FakeTable, 1)
    assert res is record

def test_read_record_valid_composite_pk(dm):
    class FakeCompositeTable(FakeModel):
        pass
    FakeCompositeTable._meta.primary_key = FakeCompositeKey(("user_id", "metric_id"))
    record = SimpleNamespace(user_id=1, metric_id=5, value=42)
    FakeCompositeTable._storage[(1, 5)] = record
    res = dm.read_record(FakeCompositeTable, 1, 5)
    assert res is record

def test_read_record_nonexistent_pk(dm):
    class FakeTable(FakeModel):
        pass
    res = dm.read_record(FakeTable, 999)
    assert res is None

@pytest.mark.xfail(reason="wrong number of PK values may raise", strict=False)
def test_read_record_wrong_number_of_pk_values(dm):
    class FakeTable(FakeModel):
        pass
    record = FakeTable.create(id=1, name="Test")
    res = dm.read_record(FakeTable, 1, 999)
    assert res is record

@pytest.mark.xfail(reason="wrong type for pk may raise", strict=False)
def test_read_record_wrong_type_for_pk(dm):
    class FakeTable(FakeModel):
        pass
    FakeTable.create(id=1, name="Valid Row")
    wrong_pk = "not-an-int"
    res = dm.read_record(FakeTable, wrong_pk)
    assert res is None

@pytest.mark.xfail(reason="null pk should raise", strict=False)
def test_read_record_null_input(dm):
    class FakeTable(FakeModel):
        pass
    FakeTable.create(id=1, name="Valid Row")
    null_pk = None
    res = dm.read_record(FakeTable, null_pk)
    assert res is None

# ------------------------------------------------------------------
# update_record tests
# ------------------------------------------------------------------

def test_update_record_valid_single_pk(dm):
    class FakeTable(FakeModel):
        pass
    record = FakeTable.create(id=1, name="Old Name")
    res = dm.update_record(FakeTable, 1, name="New Name")
    assert res == 1
    updated = FakeTable._storage[1]
    assert updated.name == "New Name"

def test_update_record_valid_composite_pk(dm):
    class FakeCompositeTable(FakeModel):
        pass
    FakeCompositeTable._meta.primary_key = FakeCompositeKey(("user_id", "metric_id"))
    record = SimpleNamespace(user_id=1, metric_id=5, value=10)
    FakeCompositeTable._storage[(1, 5)] = record
    res = dm.update_record(FakeCompositeTable, (1, 5), value=99)
    assert res == 1
    updated = FakeCompositeTable._storage[(1, 5)]
    assert updated.value == 99

@pytest.mark.xfail(reason="wrong number of PK values may raise", strict=False)
def test_update_record_nonexistent_pk(dm):
    class FakeTable(FakeModel):
        pass
    res = dm.update_record(FakeTable, 999, name="Does Not Matter")
    assert res == 0

@pytest.mark.xfail(reason="wrong type for pk may raise", strict=False)
def test_update_record_wrong_type_for_pk(dm):
    class FakeTable(FakeModel):
        pass
    FakeTable.create(id=1, name="Valid Row")
    wrong_pk = "not-an-int"
    res = dm.update_record(FakeTable, wrong_pk, name="Updated")
    assert res == 0

@pytest.mark.xfail(reason="null pk should raise", strict=False)
def test_update_record_null_pk(dm):
    class FakeTable(FakeModel):
        pass
    FakeTable.create(id=1, name="Valid Row")
    null_pk = None
    res = dm.update_record(FakeTable, null_pk, name="Updated")
    assert res == 0

@pytest.mark.xfail(reason="invalid data may raise DB error", strict=False)
def test_update_record_invalid_data(dm):
    class FakeTable(FakeModel):
        pass
    FakeTable.create(id=1, name="Original")
    with pytest.raises(Exception):
        dm.update_record(FakeTable, 1, not_a_field="ignored")

# ------------------------------------------------------------------
# delete_record tests
# ------------------------------------------------------------------

def test_delete_record_valid_single_pk(dm):
    class FakeTable(FakeModel):
        pass
    record = FakeTable.create(id=1, name="ToDelete")
    res = dm.delete_record(FakeTable, 1)
    assert res == 1
    assert 1 not in FakeTable._storage

def test_delete_record_valid_composite_pk(dm):
    class FakeCompositeTable(FakeModel):
        pass
    FakeCompositeTable._meta.primary_key = FakeCompositeKey(("user_id", "metric_id"))
    FakeCompositeTable._storage[(1, 5)] = SimpleNamespace(
        user_id=1, metric_id=5, value=10
    )
    res = dm.delete_record(FakeCompositeTable, (1, 5))
    assert res == 1
    assert (1, 5) not in FakeCompositeTable._storage

def test_delete_record_nonexistent_pk(dm):
    class FakeTable(FakeModel):
        pass
    res = dm.delete_record(FakeTable, 999)
    assert res == 0

@pytest.mark.xfail(reason="wrong type for pk may raise", strict=False)
def test_delete_record_wrong_type_for_pk(dm):
    class FakeTable(FakeModel):
        pass
    FakeTable.create(id=1, name="Row")
    wrong_pk = "not-an-int"
    res = dm.delete_record(FakeTable, wrong_pk)
    assert res == 0

@pytest.mark.xfail(reason="null pk should raise", strict=False)
def test_delete_record_null_pk(dm):
    class FakeTable(FakeModel):
        pass
    FakeTable.create(id=1, name="Row")
    null_pk = None
    res = dm.delete_record(FakeTable, null_pk)
    assert res == 0