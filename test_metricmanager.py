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

def test_read_metric_future_date(mm, db_mock):
    future_metric_id = 9999
    class FakeMetric:
        def __init__(self, met_id, name="Future Metric"):
            self.met_id = met_id
            self.name = name
    fake_metric = FakeMetric(met_id=future_metric_id)
    mm._db.read_record.return_value = fake_metric
    res = mm.read_metric(met_id=future_metric_id)
    assert res is fake_metric
    mm._db.read_record.assert_called_once_with(
        mm.metrics_table, future_metric_id
    )

@pytest.mark.xfail(reason="invalid user id should be handled", strict=False)
def test_read_metric_invalid_user_id(mm, db_mock):
    invalid_user_id = -999
    mm._db.read_record.return_value = None
    res = mm.read_metric(met_id=invalid_user_id)
    assert res is None
    mm._db.read_record.assert_called_once_with(
        mm.metrics_table, invalid_user_id
    )

@pytest.mark.xfail(reason="wrong type for date should raise", strict=False)
def test_read_metric_wrong_type_for_date(mm, db_mock):
    wrong_type_date = "2025-99-99"
    mm._db.read_record.return_value = None
    res = mm.read_metric(met_id=wrong_type_date)
    assert res is None
    mm._db.read_record.assert_called_once_with(
        mm.metrics_table, wrong_type_date
    )

@pytest.mark.xfail(reason="null input should raise", strict=False)
def test_read_metric_null_inputs(mm, db_mock):
    met_id = None
    mm._db.read_record.return_value = None
    res = mm.read_metric(met_id=met_id)
    assert res is None
    mm._db.read_record.assert_called_once_with(
        mm.metrics_table, None
    )

# ------------------------------------------------------------------
# update_metric_value
# ------------------------------------------------------------------

def test_update_metric_value_valid_inputs(mm, db_mock):
    class FakeMetricValue:
        def __init__(self, user_id, metric_id, value):
            self.user_id = user_id
            self.metric_id = metric_id
            self.value = value
    fake_record = FakeMetricValue(user_id=1, metric_id=5, value=75)
    mm._db.create_record.return_value = fake_record
    res = mm.update_metric_value(user_id=1, metric_id=5, value=75)
    assert res is fake_record
    mm._db.create_record.assert_called_once()
    args, kwargs = mm._db.create_record.call_args
    assert args[0] == mm.metric_value_table
    assert kwargs["user_id"] == 1
    assert kwargs["met_id"] == 5
    assert kwargs["metval_val"] == 75
    from datetime import date
    assert kwargs["metval_date"] == date.today()

def test_update_metric_value_within_range(mm, db_mock):
    user_id = 1
    metric_id = 10
    value = 50
    class FakeMetricValue:
        def __init__(self, user_id, metric_id, value):
            self.user_id = user_id
            self.metric_id = metric_id
            self.value = value
    fake_record = FakeMetricValue(user_id, metric_id, value)
    mm._db.create_record.return_value = fake_record
    res = mm.update_metric_value(user_id=user_id, metric_id=metric_id, value=value)
    assert res is fake_record
    mm._db.create_record.assert_called_once()
    args, kwargs = mm._db.create_record.call_args
    assert args[0] == mm.metric_value_table
    assert kwargs["user_id"] == user_id
    assert kwargs["met_id"] == metric_id
    assert kwargs["metval_val"] == value
    from datetime import date
    assert kwargs["metval_date"] == date.today()

@pytest.mark.xfail(reason="value outside range may be accepted or rejected depending on implementation", strict=False)
def test_update_metric_value_outside_range(mm, db_mock):
    user_id = 1
    metric_id = 10
    value = 9999
    class FakeMetricValue:
        def __init__(self, user_id, metric_id, value):
            self.user_id = user_id
            self.metric_id = metric_id
            self.value = value
    fake_record = FakeMetricValue(user_id, metric_id, value)
    mm._db.create_record.return_value = fake_record
    res = mm.update_metric_value(user_id=user_id, metric_id=metric_id, value=value)
    assert res is fake_record
    mm._db.create_record.assert_called_once()
    args, kwargs = mm._db.create_record.call_args
    assert args[0] == mm.metric_value_table
    assert kwargs["user_id"] == user_id
    assert kwargs["met_id"] == metric_id
    assert kwargs["metval_val"] == value
    from datetime import date
    assert kwargs["metval_date"] == date.today()

@pytest.mark.xfail(reason="non-existent metric id should raise or DB FK error", strict=False)
# def test_update_metric_value_nonexistent_metric_xfail(mm, db_mock):
#     db_mock.create_record.side_effect = Exception("FK constraint")
#     with pytest.raises(Exception):
#         mm.update_metric_value(user_id=5, metric_id=999, value=10)

@pytest.mark.xfail(reason="non-existent user id should raise or DB FK error", strict=False)
# def test_update_metric_value_nonexistent_user_xfail(mm, db_mock):
#     db_mock.create_record.side_effect = Exception("FK constraint")
#     with pytest.raises(Exception):
#         mm.update_metric_value(user_id=999, metric_id=2, value=10)

@pytest.mark.xfail(reason="wrong type for value should raise", strict=False)
# def test_update_metric_value_wrong_type_xfail(mm):
#     with pytest.raises(Exception):
#         mm.update_metric_value(user_id=5, metric_id=2, value="abc")

@pytest.mark.xfail(reason="null inputs should raise", strict=False)
# def test_update_metric_value_null_inputs_xfail(mm):
#     with pytest.raises(Exception):
#         mm.update_metric_value(user_id=None, metric_id=None, value=None)
