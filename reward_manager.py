class Reward:
    def __init__(self):
        self._name = ""
        self._description = ""
        self._points = 0
        self._unlocked = False

    @property
    def name(self) -> str:
        return self._name

    @property
    def description(self) -> str:
        return self._description

    @property
    def points(self) -> int:
        return self._points

    @property
    def unlocked(self) -> bool:
        # is this reward unlocked for the user?
        return self._unlocked

    @name.setter
    def name(self, new_name: str) -> None:
        # enforce nonempty and length limit
        if not new_name or not new_name.strip():
            raise ValueError("Reward name cannot be empty")
        if len(new_name) > 50:
            raise ValueError("Reward name cannot exceed 50 characters")
        self._name = new_name

    @description.setter
    def description(self, new_description: str) -> None:
        # cap description length
        if new_description and len(new_description) > 250:
            raise ValueError("Reward description cannot exceed 250 characters")
        self._description = new_description

    @points.setter
    def points(self, new_points: int) -> None:
        # must be zero or positive
        if new_points < 0:
            raise ValueError("Reward points cannot be negative")
        self._points = new_points

    @unlocked.setter
    def unlocked(self, new_unlocked: bool) -> None:
        self._unlocked = new_unlocked

    def unlock(self) -> None:
        self._unlocked = True

    def lock(self) -> None:
        self._unlocked = False


class RewardManager:
    def __init__(self) -> None:
        self._rewards: list = []

    @property
    def rewards(self) -> list:
        return self._rewards

    def add_reward(self, reward: Reward) -> None:
        # only Reward instances allowed
        if not isinstance(reward, Reward):
            raise TypeError("Expected a reward object")
        self._rewards.append(reward)

    def remove_reward(self, index: int) -> None:
        # remove an entry by index, raises if out of range
        if index < 0 or index >= len(self._rewards):
            raise IndexError("Reward index out of range")
        self._rewards.pop(index)

    def find_reward(self, reward_name: str) -> 'Reward | None':
        # lookup an existing reward by name (case‑insensitive)
        for reward in self._rewards:
            if reward.name.lower() == reward_name.lower():
                return reward
        return None

    def reward_exists(self, reward_name: str) -> bool:
        # check presence of a reward via name
        return self.find_reward(reward_name) is not None

    def update_reward(self, index: int, name: str = None, description: str = None, points: int = None) -> None:
        # update individual fields for a stored reward
        if index < 0 or index >= len(self._rewards):
            raise IndexError("Reward index out of range")
        reward = self._rewards[index]
        if name is not None:
            reward.name = name
        if description is not None:
            reward.description = description
        if points is not None:
            reward.points = points

    def get_all_rewards(self) -> list:
        # return internal reward list (mutable)
        return self._rewards

    def show_rewards(self) -> None:
        # print formatted list for debugging/UI
        if not self._rewards:
            print("No rewards available.")
            return
        for index, reward in enumerate(self._rewards):
            status = "Unlocked" if reward.unlocked else "Locked"
            print(
                f"[{index}] {reward.name}: {reward.description} | "
                f"Points: {reward.points} | Status: {status}"
            )


# challenge item, links to a reward when completed
class Challenge:
    def __init__(self) -> None:
        # initialize blank challenge
        self._name = ""
        self._description = ""
        self._reward = None
        self._completed = False

    @property
    def name(self) -> str:
        return self._name

    @property
    def description(self) -> str:
        return self._description

    @property
    def reward(self) -> 'Reward | None':
        # attached reward object (may be None)
        return self._reward

    @property
    def completed(self) -> bool:
        # completion flag
        return self._completed

    @name.setter
    def name(self, new_name: str) -> None:
        if not new_name or not new_name.strip():
            raise ValueError("Challenge name cannot be empty")
        self._name = new_name

    @description.setter
    def description(self, new_description: str) -> None:
        self._description = new_description

    @reward.setter
    def reward(self, new_reward: 'Reward | None') -> None:
        if new_reward is not None and not isinstance(new_reward, Reward):
            raise TypeError("Expected a Reward object")
        self._reward = new_reward

    @completed.setter
    def completed(self, new_completed: bool) -> None:
        # toggle completion
        self._completed = new_completed

    def complete(self) -> 'Reward | None':
        # mark done and give back the reward
        self._completed = True
        return self._reward

    def reset(self) -> None:
        # undo completion
        self._completed = False