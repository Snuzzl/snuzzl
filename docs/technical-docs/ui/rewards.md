# Rewards UI

## Main Files

1. app/ui/ui_rewards.py
2. app/ui/ui_challenges.py (embedded reward block)

The rewards UI shows what can be claimed, what is already claimed, and what remains blocked until challenge completion.

It reflects backend claim decisions directly. If a reward already exists for the user, the UI keeps a stable claimed state. If challenge requirements are not complete, claim attempts return clear feedback instead of failing silently.

## Routes Used By This UI

Routes used by this UI:

1. GET /rewards
2. GET /rewards/user/{user_id}
3. POST /rewards/user/{user_id}/claim

## Feedback Behavior

Feedback behavior:

1. Success feedback on claim.
2. Informational feedback on already_claimed.
3. Error feedback with server detail for 400 or 500 paths.
