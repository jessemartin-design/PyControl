# MIR_HANDOFF — MiR API control

Living device brief for the **MiR** robot API tools under the shared **PyControl** layout.  
**Update this file whenever objectives, progress, or durable facts change.**

Filename convention: device handoffs are `<TAG>_HANDOFF.md` (this file = `MIR_HANDOFF.md`). See repo-root `ALIGNMENT_HANDOFF.md`.

---

## How to update this document

1. Read at session start.
2. Edit before ending work that changes goals, status, config, or next steps.
3. Keep concise; prefer bullets.
4. Do not delete durable facts unless proven wrong — replace with a dated correction.
5. Set **Last updated** to today when you change Progress or Durable details.
6. Secrets stay in local `.env` — not here.
7. Attribute entries: `— <operator name> on <HOSTNAME>` (or `(via agent)`), from `machines/<HOSTNAME>_HANDOFF.md`.
8. Label paths that exist on only one computer with `(on <HOSTNAME>)`.
9. If docs/scripts/CLI behavior change, also update `MIR_README.md`, `docs/MIR_SETUP.md`, `docs/MIR_USER_GUIDE.md`, `docs/MIR_AUTOMATION.md`, and repo-root [`ALIGNMENT_HANDOFF.md`](../../ALIGNMENT_HANDOFF.md) if the shared pattern changed.

---

## Last updated

2026-09-30 — User confirmed smoke step 3 (`Status`) and GUI opens from `PyControl/devices/MiR_API`. Desktop backup kept (`MiR_API_backup_20260930`) until more commands are exercised. Ready for git commit. — Jesse Martin (via agent) on WS-RHCV7HYY6K

Earlier 2026-09-30 — Copied Desktop `MiR_API` into `PyControl/devices/MiR_API`. Docs + setup scripts + handoff added. Offline smoke 1–2 + 37 unit tests passed. — Jesse Martin (via agent) on WS-RHCV7HYY6K

---

## Objectives

### In scope

Reliable Python control of a MiR200 over the native REST API: CLI (`mir_command.py`) + thin tkinter GUI (`gui/`) sharing `mir/MirClient`. Easy cross-platform setup under PyControl. Safe for demos; motion only when the user confirms the area is clear.

### Out of scope (guide only)

Multi-device hub/gateway (lives in `PAI_Lab`), public-internet control, installer/Docker/systemd packaging, map embedding in the GUI (deferred).

---

## Progress

| Status | Item |
| --- | --- |
| Done | CLI + GUI + `mir/` client (pre-migration) |
| Done | Copied into `PyControl/devices/MiR_API/` |
| Done | Local `.env` copied for testing (gitignored) |
| Done | Tagged docs: `MIR_README.md`, `docs/MIR_SETUP.md`, `MIR_USER_GUIDE.md`, `MIR_AUTOMATION.md` |
| Done | `scripts/setup_*.sh` / `.ps1`; `.venv` + `requests` installed |
| Done | Smoke steps 1–2 offline (2026-09-30): code loads, scripts parse, 37 unit tests OK |
| Done | Smoke step 3: user confirmed `Status` OK from new path (2026-09-30) |
| Done | GUI opens from new path (user-verified 2026-09-30; not every command exercised) |
| Done | Desktop → `~/Desktop/MiR_API_backup_20260930` (on WS-RHCV7HYY6K); nothing deleted |
| Done | Git commit `1ec3a4f` (MiR_API package + root/Flex status notes) |
| Pending | Broader CLI/GUI command coverage from new path |
| Pending | Optional smoke step 4 (motion) — only if user asks |
| Deferred | Delete Desktop backup — keep until more commands verified + explicit yes |

### Next steps

1. Day-to-day: use `~/Documents/PyControl/devices/MiR_API` (not Desktop).
2. Exercise more CLI commands when convenient (`ListPositions`, `ListMissions`, etc.).
3. Keep the Desktop backup until you are confident and explicitly ask to delete it.
4. Motion / GUI Start only with a clear area.

---

## Smoke test (run after any change to code, paths, or setup)

Run from the device folder with `.venv` active. Steps 1–2 are agent-safe; step 3 needs the robot on Wi‑Fi; step 4 moves hardware (**ask first**).

```bash
cd /path/to/PyControl/devices/MiR_API
source .venv/bin/activate   # Windows: .\.venv\Scripts\Activate.ps1
```

| Step | Command | Pass looks like | Moves? |
| --- | --- | --- | --- |
| 1. Code loads | `python -m py_compile mir_command.py mir/client.py && python mir_command.py --help` | No errors; usage text | No |
| 2. Scripts parse (Mac/Linux) | `bash -n scripts/setup_mac.sh && bash -n scripts/setup_linux.sh` | No output | No |
| 3. Device responds | `python mir_command.py Status` | Connected banner; robot name **MiR_S1169**; host matches IP below | No |
| 4. Motion check | `GoToPosition` / `RunMission` / GUI Start | User-confirmed clear area | **Yes** |

Optional: `./run_cli.sh Status`; full re-setup: `./scripts/setup_mac.sh --non-interactive` → `SETUP OK`.  
Log the result (date + pass/fail) in **Progress**.

---

## Durable details

### Fleet / hardware

| Field | Value |
| --- | --- |
| Robot name | MiR_S1169 |
| Model | MiR200 |
| Serial | 190200015001169 |
| Software | 2.13.1.4 |
| Ethernet | Not available at this site (Wi‑Fi only) |
| Charging | Floor dock (**Charge** mission); rear cable charger for powered-off robot |

### Network

| Field | Value |
| --- | --- |
| Robot IP | `10.14.19.160` |
| Office Wi‑Fi SSID | `OPTRN-NYC1-ROBOTICS` |
| Web UI | `http://10.14.19.160` |
| REST base | `http://10.14.19.160/api/v2.0.0` |
| Ports | **80** works; HTTPS `:443` did not connect from lab Mac; `:8080` → 404 |
| Hotspot hostname | `mir.com` (only on MiR’s own Wi‑Fi) |

Do **not** set gateway to `10.14.19.160` or leave office gateway as `192.168.12.1` (MiR internal).

### Auth / config

- Same username/password as the MiR web UI, stored only in **`.env`** (`MIR_USERNAME` / `MIR_PASSWORD`).
- API Basic auth is `base64(username:sha256_hex(password))` — implemented in `mir/client.py`; do not reimplement in CLI/GUI.
- SHA-256 hash is **case-sensitive**; web UI login may not be.
- Committed example: `.env.example`. Local: `.env` (gitignored). No `config.json` for this device.

### Paths (this device)

| Path | Role |
| --- | --- |
| `mir_command.py` | CLI entry |
| `mir/` | Shared REST client |
| `gui/` | Thin tkinter GUI |
| `run_cli.*` / `run_gui.*` | Launchers (use project `.venv`) |
| `.env.example` / `.env` | Host + credentials |
| `docs/` | Setup, User, Automation, Project knowledge |
| `scripts/` | OS setup entrypoints |
| `MIR_HANDOFF.md` | This file |

---

## Migration notes

| Date | Change |
| --- | --- |
| 2026-09-30 | Copied `~/Desktop/MiR_API` → `~/Documents/PyControl/devices/MiR_API` (on WS-RHCV7HYY6K). User chose copy-first. Added tagged docs + setup scripts; `.env` copied locally for smoke test. |
| 2026-09-30 | User confirmed `Status` from new path. Renamed `~/Desktop/MiR_API` → `~/Desktop/MiR_API_backup_20260930` (on WS-RHCV7HYY6K). |

All migration rows above: Jesse Martin (via agent) on WS-RHCV7HYY6K.

**Canonical:** `PyControl/devices/MiR_API`.  
**Backup (do not delete yet):** `~/Desktop/MiR_API_backup_20260930` (on WS-RHCV7HYY6K).

---

## Undo (return to the pre-migration copy)

Backup: `~/Desktop/MiR_API_backup_20260930` (on WS-RHCV7HYY6K only — not in the zip).

1. Rename `~/Desktop/MiR_API_backup_20260930` back to `~/Desktop/MiR_API` (its `.venv` only works at that path).
2. Run health check: `cd ~/Desktop/MiR_API && ./run_cli.sh Status` (or recreate `.venv` if needed).
3. Optional: in PyControl, `git revert` the MiR migration commit(s).
4. Update this handoff to say which copy is canonical.

---

## Before you delete the backup

Do these in order; stop and ask the user if any step fails.

1. **Smoke test passes** (steps 1–3 at minimum; step 4 if motion was verified) from `PyControl/devices/MiR_API`.
2. **Nothing needed lives only in the backup:**
   - Desktop `.env` → already copied into PyControl `.env` (gitignored).
   - Desktop `.venv` → rebuild via setup script at the new path (do not copy venvs).
   - Any one-off notes/images → copy if the user wants them.
3. **Find references:** search PyControl and sibling projects for `Desktop/MiR_API` / the backup folder name; update hits. Replace **Undo** with "Undo no longer available locally; use git history" when the backup is gone.
4. **User confirms deletion** explicitly. Prefer moving to Trash.
5. **Log it** in **Progress** and **Migration notes**.

---

## Sibling projects

| Device folder | Handoff file | Status |
| --- | --- | --- |
| `Flex_Lab` | `FLEX_HANDOFF.md` | Active (PyControl) |
| `H1_Lab` | `H1_HANDOFF.md` | Active (PyControl) |
| `PAI_Lab` | (hub — separate) | `~/Documents/PAI_Lab` |

---

## Quick verify

```bash
cd /path/to/PyControl/devices/MiR_API
source .venv/bin/activate
python mir_command.py Status
```

Expect robot name **MiR_S1169** and IP **10.14.19.160** (unless the network changed — update this handoff if so).

---

## Guardrails

- Ask before any motion command or GUI Start.
- Never commit `.env` / passwords / auth headers.
- **Privacy (per `ALIGNMENT_HANDOFF.md`):** `docs/MIR_SETUP.md` / `docs/MIR_AUTOMATION.md` contain no real usernames. This handoff may hold real names, serials, IPs, and accurate paths — but **never secrets**.
- Prefer extending `mir/client.py` over reimplementing auth in CLI/GUI.
