from datetime import date, timedelta
from database_manager import DatabaseManager
   
class MetricManager:

    def __init__(self, db):
        self._db = db
    
    # Retrieve information for a metric
    def read_metric(self, met_id):
        metric = self._db.read_record(self._db.models["Metrics"], met_id)
        return metric

    # Query database for current user metric values on the given date
    def read_user_metrics(self, user_id, date):
        metrics = self._db.models["Metrics"]
        metric_value = self._db.models["MetricValue"]
                 
        query = (
            metric_value
            .select(
                metrics.met_id,
                metrics.met_name,
                metrics.met_desc,
                metrics.met_min,
                metrics.met_max,
                metric_value.metval_date,
                metric_value.metval_val
            )
            .join(metrics)
            .where(
                (metric_value.user_id == user_id) &
                (metric_value.metval_date <= date)
            )
            .order_by(metrics.met_id, metric_value.metval_date.desc())
            .distinct(metrics.met_id)
        )
        return query

    # Update the value of a metric for a user
    def update_metric_value(self, user_id, metric_id, value):
        return self._db.create_record(
            self._db.models["MetricValue"], 
            user_id = user_id,
            met_id = metric_id,
            metval_date = date.today(),
            metval_val = value
            )

def test():
    mm = MetricManager(DatabaseManager())
    print(mm.read_user_metrics(1))
