class Metric:
    
    def __init__(self):
        self._name = ""
        self._description = ""
        self._value = None
        self._min_value = 0
        self._max_value = 10
        self._reset_daily = False

    @property
    def name(self):
        return self._name
    
    @property
    def description(self):
        return self._description
    
    @property
    def value(self):
        return self._value
    
    @property
    def min_value(self):
        return self._min_value
    
    @property
    def max_value(self):
        return self._max_value
    
    @property
    def reset_daily(self):
        return self._resets_daily
    
    @name.setter
    def name(self, new_name):
        if not new_name or not new_name.strip():
            raise ValueError("Metric name cannot be empty")
        if 3 > len(new_name) > 20:
            raise ValueError("Metric name must be between 3 and 20 characters")
        self._name = new_name

    @description.setter
    def description(self, new_description):
        if not new_description or not new_description.strip():
            raise ValueError("Metric description cannot be empty")
        if len(new_description) > 250:
            raise ValueError("Metric description must be max of 250 characters")
        self._description = new_description

    @value.setter
    def value(self, new_value):
        if self.min_value > new_value > self.max_value:
            raise ValueError(f"Value must be between {self.min_value} and {self.max_value}")
        self._value = new_value

    @min_value.setter
    def min_value(self, new_min):
        self._min_value = new_min

    @max_value.setter
    def max_value(self, new_max):
        self._max_value = new_max

    @reset_daily.setter
    def reset_daily(self, reset_value):
        self._reset_daily = reset_value

    def __str__(self):
        return f"{self.name}: {self.description} | Value: {self.value}"


class MetricManager:

    def __init__(self, db):
        self._db = db

    # Create a new type of metric
    def create_metric(self, name, description, min_value=0, max_value=10, reset=True):
        # Null value and type check
        try:
            if not name or not name.strip():
                raise ValueError("Metric name cannot be empty")
            else:
                name = str(name)
            if not description or not description.strip():
                raise ValueError("Metric description cannot be empty")
            else:
                description = str(description)
            min_value = int(min_value)
            max_value = int(max_value)
            reset = bool(reset)
        except TypeError as err:
            return err
        # Validate name
        if 3 > len(name) > 20:
            raise ValueError("Metric name must be between 3 and 20 characters")
        # Validate description
        if len(description) > 250:
            raise ValueError("Metric description must be max of 250 characters")
        # Create metric in db
        self._db.create_record(
            self._db.models["Metrics"],
            met_name = name,
            met_desc = description,
            # Currently not in db:
            # met_min_value = min_value,
            # met_max_value = max_value,
            # met_reset = reset,
            met_type = 1 # Default type?
        )
        # Error if metric already exists
        # Confirm metric creation
        return f"Metric '{name}' created." 
    
    # Retrieve information for a metric
    def read_metric(self, met_id):
        return self._db.read_record(self._db.models["Metrics"], met_id)

    
    def update_metric_value(self, user_id, metric_id, value):
        return self._db.create_record(
            self._db.models["MetricValue"], 
            user_id = user_id, 
            met_id = metric_id,
            metval_date = ,
            

    def deleteMetric(self, metric_id):
        self._db.delete_record(self._db.models["MetricValue"], metric_id)

    def syncMetrics(self, user_id):
        # Update self.metrics with data from database
        pass
    
            
# def metricTest():
#     metric_manager = MetricManager()
#     print(metric_manager.createMetric("Mood", "The mood"))
#     print(metric_manager.readMetric("Mood"))
#     metric_manager.updateMetric("Mood", 2)
#     print(metric_manager.readMetric("Mood"))
#     metric_manager.deleteMetric("Mood")
#     print(metric_manager.readMetric("Mood"))

# metricTest()