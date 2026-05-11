# Challenges And Rewards API

This page documents the endpoints used by the challenge and reward flow.

Challenge endpoints:

1. GET /challenges
2. POST /challenges/{user_id}/join
3. DELETE /challenges/{user_id}/{chall_id}
4. GET /challenges/{user_id}
5. GET /challenges/{user_id}/{chall_id}/required-tasks

Reward endpoints:

1. GET /rewards
2. GET /rewards/user/{user_id}
3. POST /rewards/user/{user_id}/claim

Example join request:

```json
POST /challenges/12/join
{
  "chall_id": 7,
  "chall_sdate": "2026-05-10",
  "chall_edate": "2026-05-20"
}
```

Example claim request:

```json
POST /rewards/user/12/claim
{
  "reward_id": 4,
  "status": "Incomplete"
}
```

Example claim response:

```json
{
  "claimed": true,
  "reward_id": 4,
  "already_claimed": false
}
```

Example required tasks response:

```json
{
  "chall_id": 7,
  "tasks": [
    {
      "task_id": 1,
      "task_name": "Run",
      "task_desc": "Run 2km",
      "type_name": "Exercise",
      "assigned": true,
      "completed": false
    }
  ],
  "required_count": 1,
  "required_summary": "do 1 exercise task",
  "required_by_type": {"Exercise": 1},
  "required_progress": {
    "required_total": 1,
    "completed_total": 0,
    "completed_task_ids": [],
    "pending_task_ids": [1],
    "completion_ratio": 0.0
  },
  "requirement_kind": "tasks"
}
```

## Request Models

::: server.RewardCreate
::: server.UserRewardUpdate
::: server.RewardClaim
::: server.ChallengeJoin

## Response Notes

1. GET /rewards can include user_claimed flags when user_id is provided.
2. POST /rewards/user/{user_id}/claim returns claimed and already_claimed.
3. GET /challenges/{user_id} includes challenge status, summary, and progress fields.

## Common Errors

1. 400 when reward_id is invalid.
2. 400 when user has not joined the relevant challenge.
3. 400 when requirements are not complete.
4. 400 for join and leave validation issues.
5. 500 fallback for unexpected exceptions.

Status code summary:

1. 200 for successful reads and state-changing actions.
2. 400 for business-rule validation failures.
3. 422 for malformed request body payloads.
4. 500 for unexpected server-side failures.

In practice, these routes are used together. Challenge progress and enrollment state directly affect reward claim outcomes.

## Route Handlers

::: server.get_rewards
::: server.get_user_claimed_rewards
::: server.claim_reward
::: server.get_challenges_catalog
::: server.join_user_challenge
::: server.leave_user_challenge
::: server.get_user_challenges
::: server.get_required_challenge_tasks
