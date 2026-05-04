import account_manager, task_manager, metric_manager, competition_manager, reward_manager, social_manager, database_manager

# Initialise all managers
account_manager = account_manager.AccountManager() 
task_manager = task_manager.TaskManager()
metric_manager = metric_manager.MetricManager()
competition_manager = competition_manager.CompetitionManager()
reward_manager = reward_manager.RewardManager()
social_manager = social_manager.SocialManager()
database_manager = database_manager.DatabaseManager()
