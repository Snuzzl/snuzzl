class RewardManager:
    
    def __init__(self, database_manager=None):
        """
        Args:
            database_manager: Reference to DatabaseManager for DB operations
        """
        self.db_manager = database_manager

    def create_reward(self, reward_name, reward_description):
        """
        Args:
            reward_name (str): Name of the reward (max 50 chars)
            reward_description (str): Description of the reward (max 250 chars)
            
        Returns:
            int: reward_id if successful, None if failed
        """
        # INSERT INTO rewards (reward_name, reward_description) VALUES (...)
        # Return the new reward_id
        pass

    def give_reward(self, user_id, reward_id):
        """        
        Args:
            user_id (int): ID of the user
            reward_id (int): ID of the reward to assign
            
        Returns:
            bool: True if successful, False if failed
        """
        # INSERT INTO user_rewards (user_id, reward_id) VALUES (...)
        # Handle if already assigned
        pass

    def remove_reward(self, user_id, reward_id):
        """        
        Args:
            user_id (int): ID of the user
            reward_id (int): ID of the reward to remove
            
        Returns:
            bool: True if successful, False if failed
        """
        # DELETE FROM user_rewards WHERE user_id = ... AND reward_id = ...
        pass

    def get_user_rewards(self, user_id):
        """        
        Args:
            user_id (int): ID of the user
            
        Returns:
            list: List of reward dictionaries (reward_id, reward_name, reward_description)
        """
        # SELECT r.reward_id, r.reward_name, r.reward_description 
        # FROM rewards r 
        # JOIN user_rewards ur ON r.reward_id = ur.reward_id 
        # WHERE ur.user_id = ...
        pass

    def get_all_rewards(self):
        """        
        Returns:
            list: List of all reward dictionaries
        """
        # SELECT reward_id, reward_name, reward_description FROM rewards
        pass

    def update_reward(self, reward_id, reward_name=None, reward_description=None):
        """        
        Args:
            reward_id (int): ID of the reward to update
            reward_name (str, optional): New name for the reward
            reward_description (str, optional): New description for the reward
            
        Returns:
            bool: True if successful, False if failed
        """
        # UPDATE rewards SET ... WHERE reward_id = ...
        pass

    def reward_exists(self, reward_id):
        """
        Check if a reward exists in the system
        
        Args:
            reward_id (int): ID of the reward to check
            
        Returns:
            bool: True if exists, False otherwise
        """
        # SELECT COUNT(*) FROM rewards WHERE reward_id = ...
        pass
    
    class Reward:
        pass
        
    class Challenge:
        pass