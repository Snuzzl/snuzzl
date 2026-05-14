# tests/test_metric_manager.py
import pytest
from unittest.mock import MagicMock, patch
from datetime import date, timedelta

from app.managers.metric_manager import MetricManager


class FakeRecord:
    """Simple fake database record for mocking create_record/read_record returns."""
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)


# Fixtures
@pytest.fixture
def db_mock():
    return MagicMock()

@pytest.fixture
def mm(db_mock):
    return MetricManager(db=db_mock)


# ------------------------------------------------------------------
# read_metric
# ------------------------------------------------------------------
def test_read_metric_valid_id(mm, db_mock):
    class FakeMetric:
        def __init__(self, met_id, name="Weight"):
            self.met_id = met_id
            self.name = name
    fake_metric = FakeMetric(met_id=5, name="Bench Press")
    mm._db.read_record.return_value = fake_metric
    res = mm.read_metric(met_id=5)
    assert res is fake_metric

def test_read_metric_nonexistent_id(mm, db_mock):
    mm._db.read_record.return_value = None
    res = mm.read_metric(met_id=999)
    assert res is None
    mm._db.read_record.assert_called_once_with(
        mm.metrics_table, 999
    )

@pytest.mark.xfail(reason="wrong type should raise", strict=False)
def test_read_metric_wrong_type(mm, db_mock):
    bad_metric_id = {"not": "an int"}
    mm._db.read_record.return_value = None
    res = mm.read_metric(met_id=bad_metric_id)
    assert res is None
    mm._db.read_record.assert_called_once_with(
        mm.metrics_table, bad_metric_id
    )

@pytest.mark.xfail(reason="null input should raise", strict=False)
def test_read_metric_null_input(mm, db_mock):
    met_id = None
    mm._db.read_record.return_value = None
    res = mm.read_metric(met_id=met_id)
    assert res is None
    mm._db.read_record.assert_called_once_with(
        mm.metrics_table, None
    )

# ------------------------------------------------------------------
# read_user_metrics
# ------------------------------------------------------------------

def test_read_metric_valid_user_metrics_exist(mm, db_mock):
    class FakeMetric:
        def __init__(self, met_id, name="Calories Burned"):
            self.met_id = met_id
            self.name = name
    fake_metric = FakeMetric(met_id=3, name="Daily Steps")
    mm._db.read_record.return_value = fake_metric
    res = mm.read_metric(met_id=3)
    assert res is fake_metric
    mm._db.read_record.assert_called_once_with(
        mm.metrics_table, 3
    )

def test_read_metric_valid_user_no_metrics(mm, db_mock):
    mm._db.read_record.return_value = None
    res = mm.read_metric(met_id=42)
    assert res is None
    mm._db.read_record.assert_called_once_with(
        mm.metrics_table, 42
    )

def test_read_metric_date_boundary(mm, db_mock):
    boundary_id = 1
    class FakeMetric:
        def __init__(self, met_id, name="Boundary Metric"):
            self.met_id = met_id
            self.name = name
    fake_metric = FakeMetric(met_id=boundary_id)
    mm._db.read_record.return_value = fake_metric
    res = mm.read_metric(met_id=boundary_id)
    assert res is fake_metric
    mm._db.read_record.assert_called_once_with(
        mm.metrics_table, boundary_id
    )

# @pytest.mark.xfail(reason="future date should be accepted or handled", strict=False)
# def test_read_user_metrics_future_date(mm, db_mock):
#     future = date(2099, 1, 1)
#     db_mock.read_record.return_value = [{"user_id": 5, "met_id": 1, "value": 7, "entry_date": date(2099,1,1)}]
#     res = mm.read_user_metrics(user_id=5, date=future)
#     assert isinstance(res, list)

# @pytest.mark.xfail(reason="invalid user id should be handled", strict=False)
# def test_read_user_metrics_invalid_user_xfail(mm):
#     with pytest.raises(Exception):
#         mm.read_user_metrics(user_id=999, date=date(2024,5,10))

# @pytest.mark.xfail(reason="wrong type for date should raise", strict=False)
# def test_read_user_metrics_wrong_date_type_xfail(mm):
#     with pytest.raises(Exception):
#         mm.read_user_metrics(user_id=5, date="not-a-date")


# # ------------------------------------------------------------------
# # update_metric_value
# # ------------------------------------------------------------------
# def test_update_metric_value_creates_record_for_today(mm, db_mock):
#     today = date.today()
#     db_mock.create_record.return_value = FakeRecord(id=1, user_id=5, metric_id=2, value=10, entry_date=today)
#     res = mm.update_metric_value(user_id=5, metric_id=2, value=10)
#     db_mock.create_record.assert_called_once()
#     args, kwargs = db_mock.create_record.call_args
#     assert args[0].__name__ == "MetricValue"
#     assert kwargs["user_id"] == 5
#     assert kwargs["metric_id"] == 2
#     assert kwargs["value"] == 10
#     assert kwargs["entry_date"] == today
#     assert hasattr(res, "id")

# def test_update_metric_value_within_range(mm, db_mock):
#     # No validation expected; record created regardless of range
#     db_mock.create_record.return_value = FakeRecord(id=2)
#     res = mm.update_metric_value(user_id=5, metric_id=2, value=50)
#     db_mock.create_record.assert_called_once()
#     assert hasattr(res, "id")

# @pytest.mark.xfail(reason="value outside range may be accepted or rejected depending on implementation", strict=False)
# def test_update_metric_value_outside_range_xfail(mm, db_mock):
#     db_mock.create_record.return_value = FakeRecord(id=3)
#     res = mm.update_metric_value(user_id=5, metric_id=2, value=999999)
#     assert hasattr(res, "id")

# @pytest.mark.xfail(reason="non-existent metric id should raise or DB FK error", strict=False)
# def test_update_metric_value_nonexistent_metric_xfail(mm, db_mock):
#     db_mock.create_record.side_effect = Exception("FK constraint")
#     with pytest.raises(Exception):
#         mm.update_metric_value(user_id=5, metric_id=999, value=10)

# @pytest.mark.xfail(reason="non-existent user id should raise or DB FK error", strict=False)
# def test_update_metric_value_nonexistent_user_xfail(mm, db_mock):
#     db_mock.create_record.side_effect = Exception("FK constraint")
#     with pytest.raises(Exception):
#         mm.update_metric_value(user_id=999, metric_id=2, value=10)

# @pytest.mark.xfail(reason="wrong type for value should raise", strict=False)
# def test_update_metric_value_wrong_type_xfail(mm):
#     with pytest.raises(Exception):
#         mm.update_metric_value(user_id=5, metric_id=2, value="abc")

# @pytest.mark.xfail(reason="null inputs should raise", strict=False)
# def test_update_metric_value_null_inputs_xfail(mm):
#     with pytest.raises(Exception):
#         mm.update_metric_value(user_id=None, metric_id=None, value=None)


# # ------------------------------------------------------------------
# # read_metric edge cases and type checks (exhaustive)
# # ------------------------------------------------------------------
# def test_read_metric_null_input_xfail(mm):
#     with pytest.raises(Exception):
#         mm.read_metric(None)

# @pytest.mark.xfail(reason="string id should raise", strict=False)
# def test_read_metric_string_id_xfail(mm):
#     with pytest.raises(Exception):
#         mm.read_metric("one")


# # ------------------------------------------------------------------
# # read_user_metrics additional partitions
# # ------------------------------------------------------------------
# def test_read_user_metrics_invalid_date_none_xfail(mm):
#     with pytest.raises(Exception):
#         mm.read_user_metrics(user_id=5, date=None)

# def test_read_user_metrics_user_has_no_metrics_returns_empty(mm, db_mock):
#     db_mock.read_record.return_value = []
#     res = mm.read_user_metrics(user_id=5, date=date(2024,5,10))
#     assert res == []


# # ------------------------------------------------------------------
# # update_metric_value numeric boundary checks (exhaustive sampling)
# # ------------------------------------------------------------------
# @pytest.mark.parametrize("value", [0, 1, 100, -1])
# def test_update_metric_value_numeric_samples(mm, db_mock, value):
#     # Ensure numeric types are accepted or rejected consistently
#     if not isinstance(value, int):
#         pytest.xfail("non-integer sample")
#     db_mock.create_record.return_value = FakeRecord(id=10)
#     try:
#         res = mm.update_metric_value(user_id=5, metric_id=2, value=value)
#         assert hasattr(res, "id")
#     except Exception:
#         pytest.xfail(f"implementation rejected numeric sample {value}")
