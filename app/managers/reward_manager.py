from app.db.database_models import Challenges, Rewards, RewardType, UserRewards


class RewardManager:
    def __init__(self, database_manager=None):
        self._db = database_manager

    def _require_db(self):
        if self._db is None:
            raise RuntimeError("Database manager is not configured")
        return self._db

    def _validate_reward_name(self, reward_name):
        if not isinstance(reward_name, str) or not reward_name.strip():
            raise ValueError("reward_name must be a non-empty string")
        if len(reward_name.strip()) > 50:
            raise ValueError("reward_name cannot exceed 50 characters")

    def _require_existing_challenge(self, challenge_id):
        if not Challenges.select().where(Challenges.chall_id == challenge_id).exists():
            raise ValueError("chall_id does not exist")

    def _require_existing_reward_type(self, reward_type_id):
        if not RewardType.select().where(RewardType.type_id == reward_type_id).exists():
            raise ValueError("reward_type does not exist")

    def _normalize_reward_ids(self, reward_ids):
        if reward_ids is None:
            return None
        if isinstance(reward_ids, int):
            return [reward_ids]
        return [int(reward_id) for reward_id in reward_ids]

    def create_reward(self, data):
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
        return self._require_db().read_record(Rewards, reward_id)

    def get_rewards(self, challenge_id=None):
        if challenge_id is None:
            return list(Rewards.select())
        return list(Rewards.select().where(Rewards.chall_id == challenge_id))

    def get_all_rewards(self):
        return self.get_rewards()

    def update_reward(self, data):
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
        db = self._require_db()
        if db.read_record(Rewards, reward_id) is None:
            return 0
        return db.delete_record(Rewards, reward_id)

    def view_user_rewards(self, user_id):
        query = (
            Rewards
            .select(Rewards)
            .join(UserRewards, on=(Rewards.reward_id == UserRewards.reward_id))
            .where(UserRewards.user_id == user_id)
        )
        return list(query)

    def claim_reward(self, user_id, reward_id, status="Incomplete"):
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
            target_reward_ids = [reward_id for reward_id in normalized_reward_ids if reward_id in user_reward_ids]
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