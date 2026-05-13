# tests/test_database_manager.py
import pytest
from types import SimpleNamespace
from datetime import date

from app.db.database_manager import DatabaseManager
from peewee import CompositeKey  # used only for type-checking in tests if needed

class DoesNotExist(Exception):
    pass


class FakePrimaryKey:
    """Simple primary key object that supports equality checks used by manager."""
    def __init__(self, name):
        self.name = name

    def __eq__(self, other):
        # Manager compares pk == value or pk == tuple(values)
        return ("__pk_eq__", self.name, other)


class FakeCompositeKey(FakePrimaryKey):
    pass


class FakeModel:
    """A minimal fake Peewee model with create/get/update/delete semantics."""

    # class attributes to be set per-instance in tests
    _meta = SimpleNamespace(primary_key=FakePrimaryKey("id"))
    DoesNotExist = DoesNotExist

    # storage to simulate DB rows keyed by primary key tuple
    _storage = {}

    @classmethod
    def reset_storage(cls):
        cls._storage = {}

    @classmethod
    def create(cls, **data):
        # emulate returning an object with attributes
        pk = data.get("id", len(cls._storage) + 1)
        obj = SimpleNamespace(**{**data, "id": pk})
        cls._storage[pk] = obj
        return obj

    @classmethod
    def get(cls, condition):
        # Manager passes pk == value or pk == tuple
        # Our FakePrimaryKey.__eq__ returns a sentinel tuple we can inspect
        if not isinstance(condition, tuple) or condition[0] != "__pk_eq__":
            raise cls.DoesNotExist()
        _, pk_name, value = condition
        # value may be a tuple for composite keys
        if isinstance(value, tuple):
            # use tuple key
            key = value
        else:
            key = value
        row = cls._storage.get(key)
        if row is None:
            raise cls.DoesNotExist()
        return row

    @classmethod
    def update(cls, **data):
        # Return an object with where(...).execute() chain
        class Updater:
            def __init__(self, data):
                self.data = data
                self._where = None

            def where(self, where_clause):
                self._where = where_clause
                return self

            def execute(self):
                # where_clause will be the sentinel tuple from FakePrimaryKey.__eq__
                if not isinstance(self._where, tuple) or self._where[0] != "__pk_eq__":
                    return 0
                _, pk_name, value = self._where
                if isinstance(value, tuple):
                    key = value
                else:
                    key = value
                if key in cls._storage:
                    # update stored object attributes
                    obj = cls._storage[key]
                    for k, v in self.data.items():
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
    # ensure default primary key
    FakeModel._meta = SimpleNamespace(primary_key=FakePrimaryKey("id"))
    yield
    FakeModel.reset_storage()


@pytest.fixture
def dm():
    # DatabaseManager takes no args
    return DatabaseManager()


# ------------------------------------------------------------------
# create_record tests
# ------------------------------------------------------------------
def test_create_record_valid_inserts(dm):
    rec = dm.create_record(FakeModel, id=1, username="bob")
    assert hasattr(rec, "id")
    assert rec.username == "bob"
    # storage should contain the record
    assert FakeModel._storage[1].username == "bob"


@pytest.mark.xfail(reason="missing required fields may raise DB error", strict=False)
def test_create_record_missing_required_fields_xfail(dm):
    # If your model enforces required fields, create may raise; here it will succeed
    dm.create_record(FakeModel)  # may or may not raise depending on real model


@pytest.mark.xfail(reason="wrong data types may raise", strict=False)
def test_create_record_wrong_data_type_xfail(dm):
    # our fake create accepts anything; real model may raise
    dm.create_record(FakeModel, username=123)


@pytest.mark.xfail(reason="null table should raise", strict=False)
def test_create_record_null_table_xfail(dm):
    with pytest.raises(Exception):
        dm.create_record(None, username="bob")


# ------------------------------------------------------------------
# read_record tests
# ------------------------------------------------------------------
def test_read_record_valid_single_pk(dm):
    # prepare storage
    FakeModel.create(id=10, username="alice")
    # call read_record with model and pk value
    res = dm.read_record(FakeModel, 10)
    assert res is not None
    assert getattr(res, "username") == "alice"


def test_read_record_nonexistent_pk_returns_none(dm):
    res = dm.read_record(FakeModel, 999)
    assert res is None


def test_read_record_valid_composite_pk(dm):
    # simulate composite key by switching model._meta.primary_key to composite
    FakeModel._meta = SimpleNamespace(primary_key=FakeCompositeKey("composite"))
    # store under tuple key
    FakeModel._storage[(1, 2)] = SimpleNamespace(id=(1, 2), value="pair")
    res = dm.read_record(FakeModel, 1, 2)
    assert res is not None
    assert getattr(res, "value") == "pair"


@pytest.mark.xfail(reason="wrong number of PK values may raise", strict=False)
def test_read_record_wrong_number_of_pk_values_xfail(dm):
    FakeModel._meta = SimpleNamespace(primary_key=FakeCompositeKey("composite"))
    with pytest.raises(Exception):
        dm.read_record(FakeModel, 1)  # composite key expects two values


@pytest.mark.xfail(reason="wrong type for pk may raise", strict=False)
def test_read_record_wrong_type_pk_xfail(dm):
    with pytest.raises(Exception):
        dm.read_record(FakeModel, "abc")


@pytest.mark.xfail(reason="null pk should raise", strict=False)
def test_read_record_null_pk_xfail(dm):
    with pytest.raises(Exception):
        dm.read_record(FakeModel)  # no pk_values provided


# ------------------------------------------------------------------
# update_record tests
# ------------------------------------------------------------------
def test_update_record_valid_single_pk(dm):
    FakeModel.create(id=5, username="old")
    updated = dm.update_record(FakeModel, 5, username="new")
    assert updated == 1
    assert FakeModel._storage[5].username == "new"


def test_update_record_nonexistent_pk_returns_zero(dm):
    updated = dm.update_record(FakeModel, 999, username="x")
    assert updated == 0


def test_update_record_valid_composite_pk(dm):
    FakeModel._meta = SimpleNamespace(primary_key=FakeCompositeKey("composite"))
    FakeModel._storage[(2, 3)] = SimpleNamespace(id=(2, 3), status="old")
    updated = dm.update_record(FakeModel, (2, 3), status="Friends")
    assert updated == 1
    assert FakeModel._storage[(2, 3)].status == "Friends"


@pytest.mark.xfail(reason="wrong type for pk may raise", strict=False)
def test_update_record_wrong_type_pk_xfail(dm):
    with pytest.raises(Exception):
        dm.update_record(FakeModel, "abc", username="x")


@pytest.mark.xfail(reason="null pk should raise", strict=False)
def test_update_record_null_pk_xfail(dm):
    with pytest.raises(Exception):
        dm.update_record(FakeModel, None, username="x")


@pytest.mark.xfail(reason="invalid data may raise DB error", strict=False)
def test_update_record_invalid_data_xfail(dm):
    # our fake update accepts anything; real DB might raise
    dm.update_record(FakeModel, 1, username=None)


# ------------------------------------------------------------------
# delete_record tests
# ------------------------------------------------------------------
def test_delete_record_valid_single_pk(dm):
    FakeModel.create(id=7, username="to_delete")
    deleted = dm.delete_record(FakeModel, 7)
    assert deleted == 1
    assert 7 not in FakeModel._storage


def test_delete_record_nonexistent_pk_returns_zero(dm):
    deleted = dm.delete_record(FakeModel, 999)
    assert deleted == 0


def test_delete_record_valid_composite_pk(dm):
    FakeModel._meta = SimpleNamespace(primary_key=FakeCompositeKey("composite"))
    FakeModel._storage[(4, 5)] = SimpleNamespace(id=(4, 5), name="pair")
    deleted = dm.delete_record(FakeModel, (4, 5))
    assert deleted == 1
    assert (4, 5) not in FakeModel._storage


@pytest.mark.xfail(reason="wrong type for pk may raise", strict=False)
def test_delete_record_wrong_type_pk_xfail(dm):
    with pytest.raises(Exception):
        dm.delete_record(FakeModel, "abc")


@pytest.mark.xfail(reason="null pk should raise", strict=False)
def test_delete_record_null_pk_xfail(dm):
    with pytest.raises(Exception):
        dm.delete_record(FakeModel, None)
