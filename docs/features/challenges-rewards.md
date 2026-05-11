# Challenges And Rewards

This section covers the path from joining a challenge to claiming its reward.

## Typical Flow

1. A user browses available challenges.
2. They join one challenge.
3. They complete tasks that match the required task types.
4. The system recalculates progress and status.
5. The user claims a reward or is told it was already claimed.

On the backend, this area is handled by challenge routes under /challenges and reward routes under /rewards, backed by ChallengeManager and RewardManager. Reward checks also run after relevant task-completion actions in server.py.

One key design choice is that completion is based on required task types rather than a single hardcoded task ID path. This keeps the feature flexible while still enforcing the challenge rules.

## Backend Overview

On the backend, challenge routes and reward routes are handled separately but work together. The managers coordinate progress tracking, status calculation, and reward awarding.

## UI Integration

The UI relies on a few core values from the API:

1. Challenge summary fields like required_count and required_summary.
2. Progress fields like required_total, completed_total, pending_task_ids, and completion_ratio.
3. Reward claim state such as user_claimed and already_claimed.

## Important Rules

1. A reward cannot be claimed unless the user is enrolled in the related challenge.
2. A reward cannot be claimed unless status is completed.
3. Join requests must pass date validation, including valid ordering.

This feature also handles repeated actions cleanly. For example, a second claim attempt should return a stable already claimed result instead of creating duplicate reward state.
