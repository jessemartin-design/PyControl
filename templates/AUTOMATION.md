# __DEVICE_NAME__ — Automation Brief

Upload this file so an agent can set up `__DEVICE_NAME__` from a terminal.

## Path rule

Device root = directory containing `__CLI_MODULE__` and `config.example.json`.  
Never hard-code a single user’s home path. Prefer `~/PyControl/devices/__DEVICE_NAME__`.

## Permission gate

If `PyControl` is missing, **ask** before creating `~/PyControl` (or Windows equivalent).

## Setup

| OS | Script |
| --- | --- |
| macOS | `scripts/setup_mac.sh` |
| Linux | `scripts/setup_linux.sh` |
| Windows | `scripts/setup_windows.ps1` |

Prefer non-interactive with an explicit host when automating. Default host selection is **manual**, not discover.

## Verify with the user

1. `__PING_COMMAND__`
2. One read-only status command
3. Ask before any motion / wet / destructive action

## Shared process

See repo-root `ALIGNMENT_HANDOFF.md`.
