from datetime import date, timedelta
from database_manager import DatabaseManager
   
class MetricManager:

    def __init__(self, db):
        self._db = db
    
    # Retrieve information for a metric
    def read_metric(self, met_id):
        metric = self._db.read_record(self._db.models["Metrics"], met_id)
        return metric

    # Query database for current user metric values
    def read_user_metrics(self, user_id):
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
            .where(metric_value.user_id == user_id)
            .order_by(metrics.met_id, metric_value.metval_date.desc())
            .distinct(metrics.met_id)
        )
        return query

    # Query database for user metric values in a given time period
    def read_user_metric_recap(self, user_id, start_date, end_date=None):
        metrics = self._db.models["Metrics"]
        metric_value = self._db.models["MetricValue"]

        # Default end_date is 7 days after start_date
        if not end_date:
            end_date = start_date + timedelta(days=7)
                 
        query = (
            metric_value
            .select(
                metrics.met_id,
                metrics.met_name,
                metric_value.metval_date,
                metric_value.metval_val
            )
            .join(metrics)
            .where(
                (metric_value.user_id == user_id) &
                (metric_value.metval_date.between(start_date, end_date))
            )
        )
        return query
    
    # Iterate through user metric query results to display each metric and its value
    def show_user_metrics(self, user_id, end_date=None, start_date=None):
        metrics = self.read_user_metrics(user_id, end_date, start_date)
        if not metrics:
            print("No user metrics found.")
            return
        
        for entry in metrics:
            print(f"{entry.met_id.met_name}: {entry.metval_val}")

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
