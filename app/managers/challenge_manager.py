from datetime import date, timedelta
from app.db.database_models import Challenges, UserChallenges, TaskChallenges, UserTask, Tasks, TaskType, CustomTasks, Rewards, UserRewards


class ChallengeManager:
    """Manage challenge enrollment, status, and required task progress."""

    def __init__(self, db=None):
        """Initialize challenge manager.

        Args:
            db: Database manager used for CRUD operations.
        """
        self._db = db

    def _require_db(self):
        """Return configured database manager.

        Returns:
            object: Database manager instance.

        Raises:
            RuntimeError: If database manager is not configured.
        """
        if self._db is None:
            raise RuntimeError("Database manager is not configured")
        return self._db

    def _parse_date(self, value, field_name):
        """Parse a date value from string or date instance.

        Args:
            value (str | date | None): Incoming date value.
            field_name (str): Field name used in validation messages.

        Returns:
            date | None: Parsed date value.

        Raises:
            ValueError: If input cannot be parsed as YYYY-MM-DD.
        """
        if value is None:
            return None
        if isinstance(value, date):
            return value
        if isinstance(value, str):
            try:
                return date.fromisoformat(value)
            except ValueError as exc:
                raise ValueError(f"{field_name} must be YYYY-MM-DD") from exc
        raise ValueError(f"{field_name} must be YYYY-MM-DD")

    def _require_existing_challenge(self, chall_id):
        """Ensure challenge ID exists.

        Args:
            chall_id (int): Challenge ID.

        Raises:
            ValueError: If challenge does not exist.
        """
        if self._require_db().read_record(Challenges, chall_id) is None:
            raise ValueError("chall_id does not exist")

    def get_all_challenges(self):
        """Fetch all available challenges.

        Returns:
            list: Challenge model records.
        """
        return list(Challenges.select())

    def get_user_challenges(self, user_id):
        """Fetch challenge enrollments for a user.

        Args:
            user_id (int): User ID.

        Returns:
            list: UserChallenges rows joined with challenge records.
        """
        query = (
            UserChallenges
            .select(UserChallenges, Challenges)
            .join(Challenges)
            .where(UserChallenges.user_id == user_id)
        )
        return list(query)

    def get_required_task_progress(self, user_id, chall_id):
        """Calculate progress against a challenge's required tasks.

        Progress is measured by required task type counts, so matching tasks
        in the same categories count toward completion.

        Args:
            user_id (int): User ID.
            chall_id (int): Challenge ID.

        Returns:
            dict: Progress details including required/completed totals,
                completed IDs, pending IDs, and completion ratio.
        """
        self._require_existing_challenge(chall_id)

        required_rows = (
            Tasks
            .select(Tasks.task_id, Tasks.type_id)
            .join(TaskChallenges, on=(TaskChallenges.task_id == Tasks.task_id))
            .where(TaskChallenges.chall_id == chall_id)
        )
        required_ids = [row.task_id for row in required_rows]
        required_type_counts = {}
        for row in required_rows:
            type_id = row.type_id_id
            required_type_counts[type_id] = required_type_counts.get(type_id, 0) + 1
        unique_required_ids = sorted(set(required_ids))

        if not unique_required_ids:
            return {
                "required_total": 0,
                "completed_total": 0,
                "completed_task_ids": [],
                "pending_task_ids": [],
                "completion_ratio": 0.0,
            }

        completed_required_task_ids = {
            row.task_id_id
            for row in UserTask.select(UserTask.task_id).where(
                (UserTask.user_id == user_id)
                & (UserTask.task_id.in_(unique_required_ids))
                & (UserTask.task_complete == True)
            )
            if row.task_id_id is not None
        }

        # Progress is counted by required type so users can complete matching tasks
        # without having to complete one exact hardcoded task ID.
        completed_by_type = {}
        required_type_ids = list(required_type_counts.keys())
        if required_type_ids:
            predefined_rows = (
                UserTask
                .select(UserTask.task_id, Tasks.type_id)
                .join(Tasks, on=(UserTask.task_id == Tasks.task_id))
                .where(
                    (UserTask.user_id == user_id)
                    & (UserTask.task_complete == True)
                    & (UserTask.task_id.is_null(False))
                    & (Tasks.type_id.in_(required_type_ids))
                )
            )
            for row in predefined_rows:
                type_id = row.task_id.type_id_id
                completed_by_type[type_id] = completed_by_type.get(type_id, 0) + 1

            custom_rows = (
                UserTask
                .select(UserTask.cust_id, CustomTasks.type_id)
                .join(CustomTasks, on=(UserTask.cust_id == CustomTasks.cust_id))
                .where(
                    (UserTask.user_id == user_id)
                    & (UserTask.task_complete == True)
                    & (UserTask.cust_id.is_null(False))
                    & (CustomTasks.type_id.in_(required_type_ids))
                )
            )
            for row in custom_rows:
                type_id = row.cust_id.type_id_id
                completed_by_type[type_id] = completed_by_type.get(type_id, 0) + 1

        required_total = len(unique_required_ids)
        completed_total = 0
        for type_id, needed in required_type_counts.items():
            completed_total += min(needed, completed_by_type.get(type_id, 0))

        completed_total = min(completed_total, required_total)
        completed_sorted = sorted(completed_required_task_ids)
        pending_sorted = [task_id for task_id in unique_required_ids if task_id not in completed_required_task_ids]

        return {
            "required_total": required_total,
            "completed_total": completed_total,
            "completed_task_ids": completed_sorted,
            "pending_task_ids": pending_sorted,
            "completion_ratio": (completed_total / required_total) if required_total else 0.0,
        }

    def get_user_challenge_status(self, user_id, chall_id, chall_edate):
        """Resolve user challenge status as active, completed, or failed.

        Args:
            user_id (int): User ID.
            chall_id (int): Challenge ID.
            chall_edate (date): Enrollment challenge end date.

        Returns:
            str: One of "completed", "failed", or "active".
        """
        # Once any reward for this challenge is awarded, keep status completed.
        already_awarded = (
            UserRewards
            .select()
            .join(Rewards, on=(UserRewards.reward_id == Rewards.reward_id))
            .where((UserRewards.user_id == user_id) & (Rewards.chall_id == chall_id))
            .exists()
        )
        if already_awarded:
            return "completed"

        progress = self.get_required_task_progress(user_id, chall_id)
        if progress["required_total"] > 0 and progress["completed_total"] >= progress["required_total"]:
            return "completed"

        if date.today() > chall_edate:
            return "failed"
        return "active"

    def join_challenge(self, user_id, chall_id, chall_sdate=None, chall_edate=None):
        """Enroll a user in a challenge.

        Args:
            user_id (int): User ID.
            chall_id (int): Challenge ID.
            chall_sdate (str | date | None): Optional start date.
            chall_edate (str | date | None): Optional end date.

        Returns:
            object: Created UserChallenges row.

        Raises:
            ValueError: If challenge does not exist, user is already enrolled,
                or date range is invalid.
        """
        db = self._require_db()
        self._require_existing_challenge(chall_id)

        existing = db.read_record(UserChallenges, user_id, chall_id)
        if existing is not None:
            raise ValueError("user is already enrolled in this challenge")

        start_date = self._parse_date(chall_sdate, "chall_sdate") or date.today()
        end_date = self._parse_date(chall_edate, "chall_edate") or (start_date + timedelta(days=7))

        if end_date < start_date:
            raise ValueError("chall_edate must be on or after chall_sdate")

        return db.create_record(
            UserChallenges,
            user_id=user_id,
            chall_id=chall_id,
            chall_sdate=start_date,
            chall_edate=end_date,
        )

    def leave_challenge(self, user_id, chall_id):
        """Remove a user's enrollment from a challenge.

        Args:
            user_id (int): User ID.
            chall_id (int): Challenge ID.

        Returns:
            bool: True when unenrollment succeeds.

        Raises:
            ValueError: If user is not enrolled in challenge.
        """
        db = self._require_db()
        existing = db.read_record(UserChallenges, user_id, chall_id)
        if existing is None:
            raise ValueError("user is not enrolled in this challenge")
        db.delete_record(UserChallenges, (user_id, chall_id))
        return True

    def get_required_task_summary(self, chall_id):
        """Build a summary of required tasks for a challenge.

        Args:
            chall_id (int): Challenge ID.

        Returns:
            dict: Required task count, summary string, type counts,
                and required task identifiers/names.
        """
        self._require_existing_challenge(chall_id)
        task_rows = (
            Tasks
            .select(Tasks.task_id, Tasks.task_name, TaskType.type_name)
            .join(TaskType, on=(Tasks.type_id == TaskType.type_id))
            .join(TaskChallenges, on=(TaskChallenges.task_id == Tasks.task_id))
            .where(TaskChallenges.chall_id == chall_id)
            .order_by(Tasks.task_id)
        )

        type_counts = {}
        task_ids = []
        task_names = []
        for row in task_rows:
            task_ids.append(row.task_id)
            task_names.append(row.task_name)
            type_counts[row.type_id.type_name] = type_counts.get(row.type_id.type_name, 0) + 1

        if not task_ids:
            return {
                "count": 0,
                "summary": "no required tasks configured",
                "by_type": {},
                "task_ids": [],
                "task_names": [],
            }

        parts = []
        for type_name, count in sorted(type_counts.items()):
            label = f"{count} {type_name.lower()} task"
            if count != 1:
                label += "s"
            parts.append(label)

        return {
            "count": len(task_ids),
            "summary": "do " + ", ".join(parts),
            "by_type": type_counts,
            "task_ids": task_ids,
            "task_names": task_names,
        }

    def get_required_tasks_for_user(self, user_id, chall_id):
        """Return required tasks and user assignment/completion state.

        Args:
            user_id (int): User ID.
            chall_id (int): Challenge ID.

        Returns:
            list[dict]: Required task records annotated with assigned and
                completed flags for the user.
        """
        self._require_existing_challenge(chall_id)

        required_ids = [
            link.task_id_id
            for link in TaskChallenges.select().where(TaskChallenges.chall_id == chall_id)
        ]
        unique_required_ids = sorted(set(required_ids))
        if not unique_required_ids:
            return []

        task_rows = (
            Tasks
            .select(Tasks.task_id, Tasks.task_name, Tasks.task_desc, TaskType.type_name)
            .join(TaskType, on=(Tasks.type_id == TaskType.type_id))
            .where(Tasks.task_id.in_(unique_required_ids))
        )
        task_map = {
            row.task_id: {
                "task_id": row.task_id,
                "task_name": row.task_name,
                "task_desc": row.task_desc,
                "type_name": row.type_id.type_name,
            }
            for row in task_rows
        }

        assigned_rows = (
            UserTask
            .select(UserTask.task_id, UserTask.task_complete)
            .where(
                (UserTask.user_id == user_id)
                & (UserTask.task_id.in_(unique_required_ids))
            )
        )
        assigned_map = {
            row.task_id_id: bool(row.task_complete)
            for row in assigned_rows
            if row.task_id_id is not None
        }

        result = []
        for task_id in unique_required_ids:
            base = task_map.get(task_id, {"task_id": task_id, "task_name": f"task #{task_id}", "task_desc": None, "type_name": "unknown"})
            result.append({
                **base,
                "assigned": task_id in assigned_map,
                "completed": assigned_map.get(task_id, False),
            })
        return result