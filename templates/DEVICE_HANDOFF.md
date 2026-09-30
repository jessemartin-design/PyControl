# __DEVICE_HANDOFF_FILE__ — __DEVICE_NAME__

Living device brief under **PyControl**. Update when goals, progress, or durable facts change.

Filename must be `__DEVICE_HANDOFF_FILE__` (pattern `<TAG>_HANDOFF.md`, never bare `HANDOFF.md`).  
Everyday docs in this device package must also be tagged: `__DEVICE_TAG___README.md`, `docs/__DEVICE_TAG___SETUP.md`, `docs/__DEVICE_TAG___USER_GUIDE.md`, `docs/__DEVICE_TAG___AUTOMATION.md`.  
Put durable facts **and** any deep diagnosis / API quirks agents need in this handoff — do not keep a parallel `PROJECT_KNOWLEDGE.md`.  
See repo-root `ALIGNMENT_HANDOFF.md`.

## How to update

1. Read at session start; edit before ending meaningful work.
2. Keep concise; date **Last updated**.
3. No secrets here (passwords, API keys/tokens, Wi‑Fi passphrases stay in `config.json` / `.env`).
4. Attribute entries: `— <operator name> on <HOSTNAME>` (or `(via agent)`), from `machines/<HOSTNAME>_HANDOFF.md`.
5. Label paths that exist on only one computer with `(on <HOSTNAME>)`.
6. This file ships in the team zip — real names, serials, IPs are OK; secrets are not.
7. If shared pattern changes, update repo-root `ALIGNMENT_HANDOFF.md`.

## Last updated

YYYY-MM-DD — (describe change) — <operator> on <HOSTNAME>

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

## Smoke test (run after any change to code, paths, or setup)

Run from the device folder with `.venv` active. Order: safest first. **Ask the user before any step that moves hardware.**

| Step | Command | Pass looks like | Moves? |
| --- | --- | --- | --- |
| 1. Code loads | `python -m py_compile __CLI_MODULE__ && python __CLI_MODULE__ --help` | No errors; usage text | No |
| 2. Scripts parse (Mac/Linux) | `bash -n scripts/setup_mac.sh && bash -n scripts/setup_linux.sh` | No output | No |
| 3. Device responds | `__PING_COMMAND__` | (expected output) | No |
| 4. Motion / wet check | (device-specific) | (expected output) | **Yes** |

Log the result (date + pass/fail) in **Progress**.

## Migration notes

| Date | Change |
| --- | --- |
| | |

## Undo (return to the pre-migration copy)

Backup convention: `<Folder>_backup_<YYYYMMDD>` in the same parent folder as the original. If there was no migration, write "Not applicable."

1. Rename `<backup folder>` back to `<original folder>` (its `.venv` only works at the original path).
2. Run its health check: (command).
3. Optional: in PyControl, `git revert <migration commit>`.
4. Update this handoff to say which copy is canonical.

## Before you delete the backup

Do these in order; stop and ask the user if any step fails.

1. **Smoke test passes** (all steps) from `PyControl/devices/__DEVICE_NAME__`.
2. **Nothing needed lives only in the backup:**
   - (backup-only file) → (replacement, or "copy if wanted")
3. **Find references:** search PyControl and sibling projects for `<backup folder>`; update each hit to say it was deleted (date). Replace **Undo** with "Undo no longer available locally; use git history."
4. **User confirms deletion** explicitly. Prefer moving to Trash.
5. **Log it** in **Progress** and **Migration notes**.
