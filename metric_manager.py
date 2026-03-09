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

    def __init__(self):
        # Dictionary of the current users metrics, syncs with db
        # name : value 
        self._metrics = {}

    @property
    def metrics(self):
        return self._metrics

    @metrics.setter
    def metrics(self, metrics):
        self._metrics = metrics

    def createMetric(self, name, description, min_value=0, max_value=10):
        # Create a new type of metric
        # Type validation
        if type(name) != str or type(description) != str: 
            try:
                name = str(name)
                description = str(description) 
            except TypeError as err:
                return err
        # Insert new metric object to metric dictionary & database
        if name in self.metrics.keys():
            return IndexError("Create failed: Metric already exists.")
        new_metric = Metric()
        new_metric.name = name
        new_metric.description = description
        new_metric.min_value = min_value
        new_metric.max_value = max_value
        self.metrics[name] = new_metric
        # Confirm metric creation
        return f"Metric '{name}' created." 
        
    def readMetric(self, metric):
        # read metric from dictionary and/or database
        if metric in self.metrics.keys():
            return self.metrics[metric]
        else:
            return KeyError("Read failed: Metric does not exist.")


    def updateMetric(self, metric, value):
        # Update metric in dictionary & database
        if metric in self.metrics.keys():
            m = self.metrics[metric]
            if m.min_value > value > m.max_value:
                return ValueError(f"Value must be between {m.min_value} and {m.max_value}.")
            m.value = value
        else:
            return IndexError("Update failed: Metric does not exist.")

    def deleteMetric(self, metric):
        # Remove metric from dictionary & database
        if metric in self.metrics.keys():
            del self.metrics[metric]
        else:
            return KeyError("Delete failed: Metric does not exist.")

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