from datetime import date
   
class MetricManager:

    def __init__(self, db):
        self._db = db
        self.metrics_table = self._db.models["Metrics"]
        self.metric_value_table = self._db.models["MetricValue"]
    
    # Retrieve information for a metric
    def read_metric(self, met_id):
        return self._db.read_record(self.metrics_table, met_id)

    # Query database for metric information and current user metric values on the given date
    def read_user_metrics(self, user_id, date):
        query = (
            self.metric_value_table
            .select(
                self.metrics_table.met_id,
                self.metrics_table.met_name,
                self.metrics_table.met_desc,
                self.metrics_table.met_min,
                self.metrics_table.met_max,
                self.metric_value_table.metval_date,
                self.metric_value_table.metval_val
            )
            .join(self.metrics_table)
            .where(
                (self.metric_value_table.user_id == user_id) &
                (self.metric_value_table.metval_date <= date)
            )
            .order_by(self.metrics_table.met_id, self.metric_value_table.metval_date.desc())
            .distinct(self.metrics_table.met_id)
        )

        return [
            {
                "metric_id": metric.met_id.met_id,
                "metric_name": metric.met_id.met_name,
                "metric_desc": metric.met_id.met_desc,
                "metric_min": metric.met_id.met_min,
                "metric_max": metric.met_id.met_max,
                "metric_value": metric.metval_val,
                "last_updated": str(metric.metval_date)
            } 
            for metric in query
        ]

    # Update the value of a metric for a user
    def update_metric_value(self, user_id, metric_id, value):
        return self._db.create_record(
            self.metric_value_table, 
            user_id = user_id,
            met_id = metric_id,
            metval_date = date.today(),
            metval_val = value
            )
