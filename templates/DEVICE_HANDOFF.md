# __DEVICE_HANDOFF_FILE__ — __DEVICE_NAME__

Living device brief under **PyControl**. Update when goals, progress, or durable facts change.

Filename must be `__DEVICE_HANDOFF_FILE__` (pattern `<TAG>_HANDOFF.md`, never bare `HANDOFF.md`).  
See repo-root `ALIGNMENT_HANDOFF.md`.

## How to update

1. Read at session start; edit before ending meaningful work.
2. Keep concise; date **Last updated**.
3. No secrets here.
4. If shared pattern changes, update repo-root `ALIGNMENT_HANDOFF.md`.

## Last updated

YYYY-MM-DD — (describe change)

## Objectives

- (device control goals)

## Progress

| Status | Item |
| --- | --- |
| | |

## Durable details

| Field | Value |
| --- | --- |
| Network | `__WIFI_OR_NETWORK__` |
| Host | `__DEFAULT_HOST__` |
| CLI | `__CLI_MODULE__` |
| Handoff | `__DEVICE_HANDOFF_FILE__` |

## Quick verify

```bash
cd /path/to/PyControl/devices/__DEVICE_NAME__
source .venv/bin/activate
__PING_COMMAND__
```
