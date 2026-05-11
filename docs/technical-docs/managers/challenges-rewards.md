# Challenge And Reward Managers

## Files Covered Here

1. app/managers/challenge_manager.py
2. app/managers/reward_manager.py

## Overview

This part of the backend is responsible for challenge progress and reward outcomes.

ChallengeManager handles the challenge side of things: joining and leaving, required task summaries, progress tracking, and status checks. The key point is that progress is based on required task types, not only one exact task ID path.

RewardManager handles reward records and user reward state. It supports create/read/update/delete operations, and it also controls challenge reward awarding so repeated actions do not create duplicate links.

## Runtime Flow

1. A user joins a challenge.
2. The user completes tasks.
3. ChallengeManager recalculates progress and status.
4. When status is completed, RewardManager awards missing rewards.
5. Claim flow returns a consistent claimed or already claimed result.

## Important Rules

1. Claim must fail if the user is not enrolled in the challenge.
2. Claim must fail if challenge status is not completed.
3. Reward awarding for the same user/challenge must stay idempotent.
4. Validation failures should surface clear messages at route level.

## Main Payload Blocks

1. Summary: count, summary, by_type, task_ids, task_names.
2. Progress: required_total, completed_total, pending_task_ids, completion_ratio.
