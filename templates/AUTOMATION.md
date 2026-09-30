# __DEVICE_NAME__ — Automation Brief

Upload this file so an agent can set up `__DEVICE_NAME__` from a terminal.

## Path rule

Device root = directory containing `__CLI_MODULE__` and `config.example.json`.  
Never hard-code a real OS username. Prefer `~/PyControl/devices/__DEVICE_NAME__` or the path in `machines/<HOSTNAME>_HANDOFF.md`.

## Privacy scan

Fix real `/Users/<person>` paths in SETUP/AUTOMATION only.  
Do **not** scrub accurate historical paths in `__DEVICE_HANDOFF_FILE__`.

## Permission gates

- Ask before creating `~/PyControl` (or machine-handoff path).
- Ensure `machines/<HOSTNAME>_HANDOFF.md` exists; collect git identity; apply `git config` with permission.

## Setup

| OS | Script |
| --- | --- |
| macOS | `scripts/setup_mac.sh` |
| Linux | `scripts/setup_linux.sh` |
| Windows | `scripts/setup_windows.ps1` |

Host/IDs: read `__DEVICE_HANDOFF_FILE__` / config — do not hard-code lab-specific values in this brief.

## Verify with the user

1. `__PING_COMMAND__`
2. Compare identity fields to `__DEVICE_HANDOFF_FILE__`
3. Ask before any motion / wet / destructive action

## Shared process

See repo-root `ALIGNMENT_HANDOFF.md`.
