from app.db.database_models import Challenges, Rewards, RewardType, UserRewards


class RewardManager:
    """Manages creation, retrieval, updating, deletion, and claiming of rewards."""

    def __init__(self, database_manager=None):
        """Initializes the RewardManager.

        Args:
            database_manager: An instance of the database manager used for CRUD operations.
        """
        self._db = database_manager

    def _require_db(self):
        """Ensures a database manager is configured.

        Raises:
            RuntimeError: If no database manager is set.

        Returns:
            Any: The configured database manager.
        """
        if self._db is None:
            raise RuntimeError("Database manager is not configured")
        return self._db

    def _validate_reward_name(self, reward_name):
        """Validates the reward name.

        Args:
            reward_name (str): The reward name to validate.

        Raises:
            ValueError: If the name is empty or exceeds 50 characters.
        """
        if not isinstance(reward_name, str) or not reward_name.strip():
            raise ValueError("reward_name must be a non-empty string")
        if len(reward_name.strip()) > 50:
            raise ValueError("reward_name cannot exceed 50 characters")

    def _require_existing_challenge(self, challenge_id):
        """Ensures the challenge exists.

        Args:
            challenge_id (int): Challenge ID to validate.

        Raises:
            ValueError: If the challenge does not exist.
        """
        if not Challenges.select().where(Challenges.chall_id == challenge_id).exists():
            raise ValueError("chall_id does not exist")

    def _require_existing_reward_type(self, reward_type_id):
        """Ensures the reward type exists.

        Args:
            reward_type_id (int): Reward type ID to validate.

        Raises:
            ValueError: If the reward type does not exist.
        """
        if not RewardType.select().where(RewardType.type_id == reward_type_id).exists():
            raise ValueError("reward_type does not exist")

    def _normalize_reward_ids(self, reward_ids):
        """Normalizes reward IDs into a list.

        Args:
            reward_ids (int | list[int] | None): Reward IDs.

        Returns:
            list[int] | None: Normalized list of reward IDs.
        """
        if reward_ids is None:
            return None
        if isinstance(reward_ids, int):
            return [reward_ids]
        return [int(reward_id) for reward_id in reward_ids]

    def create_reward(self, data):
        """Creates a new reward.

        Args:
            data (dict): Reward fields including:
                - chall_id (int)
                - reward_name (str)
                - reward_type (int)

        Raises:
            TypeError: If data is not a dict.
            ValueError: If required fields are missing or invalid.

        Returns:
            Rewards: The created reward record.
        """
        db = self._require_db()
        if not isinstance(data, dict):
            raise TypeError("data must be a dict")

        required = {"chall_id", "reward_name", "reward_type"}
        missing = required - set(data.keys())
        if missing:
            raise ValueError(f"Missing reward fields: {', '.join(sorted(missing))}")

        self._validate_reward_name(data["reward_name"])
        self._require_existing_challenge(data["chall_id"])
        self._require_existing_reward_type(data["reward_type"])

        return db.create_record(
            Rewards,
            chall_id=data["chall_id"],
            reward_name=data["reward_name"],
            reward_type=data["reward_type"],
        )

    def get_reward(self, reward_id):
        """Fetches a single reward.

        Args:
            reward_id (int): Reward ID.

        Returns:
            Rewards | None: The reward record if found.
        """
        return self._require_db().read_record(Rewards, reward_id)

    def get_rewards(self, challenge_id=None):
        """Fetches rewards, optionally filtered by challenge.

        Args:
            challenge_id (int | None): Challenge ID to filter by.

        Returns:
            list[Rewards]: List of reward records.
        """
        if challenge_id is None:
            return list(Rewards.select())
        return list(Rewards.select().where(Rewards.chall_id == challenge_id))

    def get_all_rewards(self):
        """Fetches all rewards.

        Returns:
            list[Rewards]: All reward records.
        """
        return self.get_rewards()

    def update_reward(self, data):
        """Updates a reward.

        Args:
            data (dict): Fields to update, must include reward_id.

        Raises:
            TypeError: If data is not a dict.
            ValueError: If reward_id is missing.

        Returns:
            int: Number of updated rows (0 if none).
        """
        db = self._require_db()
        if not isinstance(data, dict):
            raise TypeError("data must be a dict")
        if "reward_id" not in data:
            raise ValueError("Missing reward_id for update")

        allowed = {"chall_id", "reward_name", "reward_type"}
        payload = {key: value for key, value in data.items() if key in allowed}
        if not payload:
            return 0

        if db.read_record(Rewards, data["reward_id"]) is None:
            return 0

        if "reward_name" in payload:
            self._validate_reward_name(payload["reward_name"])
        if "chall_id" in payload:
            self._require_existing_challenge(payload["chall_id"])
        if "reward_type" in payload:
            self._require_existing_reward_type(payload["reward_type"])

        return db.update_record(Rewards, data["reward_id"], **payload)

    def delete_reward(self, reward_id):
        """Deletes a reward.

        Args:
            reward_id (int): Reward ID.

        Returns:
            int: Number of deleted rows (0 if none).
        """
        db = self._require_db()
        if db.read_record(Rewards, reward_id) is None:
            return 0
        return db.delete_record(Rewards, reward_id)

    def view_user_rewards(self, user_id):
        """Fetches all rewards claimed by a user.

        Args:
            user_id (int): User ID.

        Returns:
            list[Rewards]: List of reward records.
        """
        query = (
            Rewards
            .select(Rewards)
            .join(UserRewards, on=(Rewards.reward_id == UserRewards.reward_id))
            .where(UserRewards.user_id == user_id)
        )
        return list(query)

    def award_challenge_rewards(self, user_id, challenge_id, status="Complete"):
        """Awards all rewards for a challenge to the user if not already awarded.

        Args:
            user_id (int): User ID.
            challenge_id (int): Challenge ID.
            status (str): Stored reward status value.

        Returns:
            int: Number of newly awarded rewards.
        """
        self._require_existing_challenge(challenge_id)

        rewards = Rewards.select().where(Rewards.chall_id == challenge_id)
        awarded = 0
        for reward in rewards:
            existing = UserRewards.get_or_none(
                (UserRewards.user_id == user_id) & (UserRewards.reward_id == reward.reward_id)
            )
            if existing is not None:
                continue
            UserRewards.create(user_id=user_id, reward_id=reward.reward_id, reward_status=status)
            awarded += 1

        return awarded

    def claim_reward(self, user_id, reward_id, status="Incomplete"):
        """Claims or unclaims a reward for a user.

        Args:
            user_id (int): User ID.
            reward_id (int): Reward ID.
            status (str): Reward status.

        Raises:
            ValueError: If reward does not exist.

        Returns:
            bool: True if claimed, False if unclaimed.
        """
        db = self._require_db()
        if db.read_record(Rewards, reward_id) is None:
            raise ValueError("reward_id does not exist")

        existing = UserRewards.get_or_none(
            (UserRewards.user_id == user_id) & (UserRewards.reward_id == reward_id)
        )
        if existing is not None:
            existing.delete_instance()
            return False

        UserRewards.create(user_id=user_id, reward_id=reward_id, reward_status=status)
        return True

    def update_user_rewards(self, user_id, reward_ids=None, **fields):
        """Updates reward fields for one or more rewards linked to a user.

        Args:
            user_id (int): User ID.
            reward_ids (int | list[int] | None): Specific reward IDs to update.
            **fields: Fields to update (reward_name, reward_type).

        Raises:
            ValueError: If reward_ids include rewards not linked to the user.

        Returns:
            int: Number of updated rows.
        """
        allowed = {"reward_name", "reward_type"}
        payload = {key: value for key, value in fields.items() if key in allowed}
        if not payload:
            return 0

        if "reward_name" in payload:
            self._validate_reward_name(payload["reward_name"])
        if "reward_type" in payload:
            self._require_existing_reward_type(payload["reward_type"])

        user_reward_ids = [reward.reward_id for reward in self.view_user_rewards(user_id)]
        if not user_reward_ids:
            return 0

        normalized_reward_ids = self._normalize_reward_ids(reward_ids)
        if normalized_reward_ids is None:
            target_reward_ids = user_reward_ids
        else:
            target_reward_ids = [
                reward_id for reward_id in normalized_reward_ids
                if reward_id in user_reward_ids
            ]
            if len(target_reward_ids) != len(set(normalized_reward_ids)):
                raise ValueError("One or more reward_ids are not linked to this user")

        if not target_reward_ids:
            return 0

        return (
            Rewards
            .update(**payload)
            .where(Rewards.reward_id.in_(target_reward_ids))
            .execute()
        )