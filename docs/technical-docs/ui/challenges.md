# Challenges UI

## Main Files

1. app/ui/ui_challenges.py
2. app/ui/challenges_utils.py

The challenges UI combines discovery and progress tracking in one screen. Users can switch between browsing available challenges and viewing joined challenges with current status and progress.

The screen logic is state driven. It tracks the active view, stores fetched payloads for redraw stability, and surfaces user feedback after actions such as join, leave, or claim.

The code is split into card builders and helper utilities. Card builders shape visible challenge and reward blocks, while utilities handle concerns such as payload normalization, date formatting, reward grouping, and status badge theme mapping.

## Routes Used By This UI

Routes used by this UI:

1. /challenges
2. /challenges/{user_id}
3. /challenges/{user_id}/join
4. /challenges/{user_id}/{chall_id}/required-tasks
5. /rewards
6. /rewards/user/{user_id}
7. /rewards/user/{user_id}/claim

## Error Handling Approach

Error handling approach:

1. HTTP responses are parsed for readable detail text.
2. Partial payloads are normalized before rendering.
3. Missing fields use fallback labels so rendering remains stable.

## Related Tests

Relevant helper behavior is tested in tests/test_challenges_utils.py.

## Challenges
::: app.ui.ui_challenges  

::: app.ui.challenges_utils  