from datetime import date
   
class MetricManager:
    """Manages retrieval and updates of metric data for users.

    This class provides an interface for interacting with metric-related
    records in the database, including reading metric definitions,
    querying user-specific metric values, and updating metric values.

    Attributes:
        _db: Database interface providing access to models and CRUD operations.
    """

    def __init__(self, db):
        """Initializes the MetricManager with a database instance.

        Args:
            db: Database interface used to access models and perform queries.
        """
        self._db = db
        self.metrics_table = self._db.models["Metrics"]
        self.metric_value_table = self._db.models["MetricValue"]

    def read_metric(self, met_id):
        """Retrieve information for a specific metric.

        Args:
            met_id (int): Unique identifier of the metric.

        Returns:
            object: Metric record corresponding to the given ID.
        """
        metric = self._db.read_record(self._db.models["Metrics"], met_id)
        return metric

    def read_user_metrics(self, user_id, date):
        """Query the latest metric values for a user up to a given date.

        Retrieves the most recent value for each metric associated with
        the specified user, where the metric value date is less than or
        equal to the provided date. Also provides the metadata for each
        metric.

        Args:
            user_id (int): Unique identifier of the user.
            date (datetime.date): Upper bound date for metric values.

        Returns:
            Query: A database query returning one row per metric, including:  
                - met_id: Metric ID  
                - met_name: Metric name  
                - met_desc: Metric description  
                - met_min: Minimum allowed value  
                - met_max: Maximum allowed value  
                - metval_date: Date of the metric value  
                - metval_val: Metric value  
        """

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

    def update_metric_value(self, user_id, metric_id, value):
        """Create a new metric value entry for a user.

        Inserts a new record representing the current value of a metric
        for a given user. The date is automatically set to today's date.

        Args:
            user_id (int): Unique identifier of the user.
            metric_id (int): Unique identifier of the metric.
            value (float | int): Value to assign to the metric.

        Returns:
            object: The created database record.
        """
        return self._db.create_record(
            self.metric_value_table, 
            user_id = user_id,
            met_id = metric_id,
            metval_date = date.today(),
            metval_val = value
            )
