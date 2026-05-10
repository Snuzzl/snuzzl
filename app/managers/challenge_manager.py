from datetime import date, timedelta
from app.db.database_models import Challenges, UserChallenges, TaskChallenges, UserTask, Tasks, TaskType


class ChallengeManager:
    def __init__(self, db=None):
        self._db = db

    def _require_db(self):
        if self._db is None:
            raise RuntimeError("Database manager is not configured")
        return self._db

    def _parse_date(self, value, field_name):
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
        if self._require_db().read_record(Challenges, chall_id) is None:
            raise ValueError("chall_id does not exist")

    def get_all_challenges(self):
        return list(Challenges.select())

    def get_user_challenges(self, user_id):
        query = (
            UserChallenges
            .select(UserChallenges, Challenges)
            .join(Challenges)
            .where(UserChallenges.user_id == user_id)
        )
        return list(query)

    def get_user_challenge_status(self, user_id, chall_id, chall_edate):
        challenge_task_ids = [
            link.task_id_id
            for link in TaskChallenges.select().where(TaskChallenges.chall_id == chall_id)
        ]

        if challenge_task_ids:
            completed_task_ids = {
                row.task_id_id
                for row in UserTask.select(UserTask.task_id).where(
                    (UserTask.user_id == user_id)
                    & (UserTask.task_id.in_(challenge_task_ids))
                    & (UserTask.task_complete == True)
                )
            }
            if len(completed_task_ids) >= len(set(challenge_task_ids)):
                return "completed"

        if date.today() > chall_edate:
            return "failed"
        return "active"

    def join_challenge(self, user_id, chall_id, chall_sdate=None, chall_edate=None):
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
        db = self._require_db()
        existing = db.read_record(UserChallenges, user_id, chall_id)
        if existing is None:
            raise ValueError("user is not enrolled in this challenge")
        db.delete_record(UserChallenges, (user_id, chall_id))
        return True

    def get_required_task_summary(self, chall_id):
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