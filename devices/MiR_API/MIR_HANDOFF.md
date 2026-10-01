# MIR_HANDOFF — MiR API control

Living device brief for the **MiR** robot API tools under the shared **PyControl** layout.  
**Update this file whenever objectives, progress, durable facts, or API/GUI behavior notes change.**

Filename convention: device handoffs are `<TAG>_HANDOFF.md` (this file = `MIR_HANDOFF.md`). See repo-root `ALIGNMENT_HANDOFF.md`.

This file is the **single agent pickup point** for MiR: status, network facts, smoke/undo, **and** API/GUI diagnosis. Everyday human docs stay in `docs/MIR_*.md`.

---

## How to update this document

1. Read at session start.
2. Edit before ending work that changes goals, status, config, API quirks, or next steps.
3. Keep sections scannable; prefer bullets and tables.
4. Do not delete durable facts unless proven wrong — replace with a dated correction.
5. Set **Last updated** to today when you change Progress or Durable / API sections.
6. Secrets stay in local `.env` — not here.
7. Attribute entries: `— <operator name> on <HOSTNAME>` (or `(via agent)`), from `machines/<HOSTNAME>_HANDOFF.md`.
8. Label paths that exist on only one computer with `(on <HOSTNAME>)`.
9. If docs/scripts/CLI behavior change, also update `MIR_README.md`, `docs/MIR_SETUP.md`, `docs/MIR_USER_GUIDE.md`, `docs/MIR_AUTOMATION.md`, and repo-root [`ALIGNMENT_HANDOFF.md`](../../ALIGNMENT_HANDOFF.md) if the shared pattern changed.

---

## Last updated

2026-10-01 — PAI_Lab retired as live hub sibling: out-of-scope hub + sibling table point to local gitignored backup `PyControl/backups/PAI_Lab_backup_20261001/`. Live `~/Documents/PAI_Lab` moved to Trash. — Jesse Martin (via agent) on WS-RHCV7HYY6K

Earlier 2026-09-30 — Consistency + GitHub-share notes in Alignment/README; ready for private-repo publish prep. — Jesse Martin (via agent) on WS-RHCV7HYY6K

Earlier 2026-09-30 — Merged former `docs/PROJECT_KNOWLEDGE.md` into this handoff (one agent entry point); deleted the duplicate file. — Jesse Martin (via agent) on WS-RHCV7HYY6K

Earlier 2026-09-30 — Removed redundant `docs/MiR_AUTOSETUP.md` stub; canonical agent brief is `docs/MIR_AUTOMATION.md` only. — Jesse Martin (via agent) on WS-RHCV7HYY6K

Earlier 2026-09-30 — User confirmed smoke step 3 (`Status`) and GUI opens from `PyControl/devices/MiR_API`. Desktop backup kept (`MiR_API_backup_20260930`) until more commands are exercised. — Jesse Martin (via agent) on WS-RHCV7HYY6K

Earlier 2026-09-30 — Copied Desktop `MiR_API` into `PyControl/devices/MiR_API`. Docs + setup scripts + handoff added. Offline smoke 1–2 + 37 unit tests passed. — Jesse Martin (via agent) on WS-RHCV7HYY6K

---

## Objectives

### In scope

Reliable Python control of a MiR200 over the native REST API: CLI (`mir_command.py`) + thin tkinter GUI (`gui/`) sharing `mir/MirClient`. Easy cross-platform setup under PyControl. Safe for demos; motion only when the user confirms the area is clear. Prefer facility Wi‑Fi so the full robot web UI stays usable (not stuck on the MiR hotspot).

### Out of scope (guide only)

Multi-device hub/gateway (retired; local-only backup at `PyControl/backups/PAI_Lab_backup_20261001/` on WS-RHCV7HYY6K), public-internet control, installer/Docker/systemd packaging, map embedding in the GUI (deferred).

### Product UX (keep unless user changes it)

- CLI: `GoToPosition <name>`, `RunMission <name>`, typo correction, live catalogs from the robot.
- GUI: separate Position / Mission dropdowns; local **draft** queue (Add / Remove / Clear / ▲▼ / drag-reorder); **Start** runs draft continuously (wait for each queue entry to finish before next); **Pause** / **Stop**; **Clear paths**; **Clear errors** only in software Error (12); no Start confirm dialog; do **not** block queueing on e-stop; no charger-leave warning in GUI (CLI still warns).
- Mission Status + Robot Status readouts (including `status.errors`). Map panel is browser-open stub only. Progress % deferred (`distance_to_next_target`).

---

## Progress

| Status | Item |
| --- | --- |
| Done | CLI + GUI + `mir/` client (pre-migration) |
| Done | Copied into `PyControl/devices/MiR_API/` |
| Done | Local `.env` copied for testing (gitignored) |
| Done | Tagged docs: `MIR_README.md`, `docs/MIR_SETUP.md`, `MIR_USER_GUIDE.md`, `MIR_AUTOMATION.md` |
| Done | Removed legacy `docs/MiR_AUTOSETUP.md` stub (use `MIR_AUTOMATION.md` only) |
| Done | Merged `docs/PROJECT_KNOWLEDGE.md` into this handoff; deleted the duplicate |
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

Optional: `./run_cli.sh Status`; unit tests (no robot): `.venv/bin/python -m unittest discover -s tests`; full re-setup: `./scripts/setup_mac.sh --non-interactive` → `SETUP OK`.  
Log the result (date + pass/fail) in **Progress**.

---

## Durable details

### Fleet / hardware

| Field | Value |
| --- | --- |
| Robot name | MiR_S1169 |
| Model | MiR200 |
| Serial | 190200015001169 |
| Software | 2.13.1.4 (`Robot-Version` header) |
| Ethernet | Not available at this site (Wi‑Fi only) |
| Charging | Floor dock (**Charge** mission); rear cable charger for powered-off robot |

**Charging notes:** Cable charger is OEM 24 VDC 10 A + rocker switch — not a laptop-style AC adapter. Plug in or flip the charge switch → robot goes to **emergency stop** by design. Observed 2026-08-18: robot still **fully powers off** on wall outlet in wired-charging mode (BMS pack disconnect, not an API/GUI keep-alive bug).

### Network

| Field | Value |
| --- | --- |
| Robot IP | `10.14.19.160` |
| Office Wi‑Fi SSID | `OPTRN-NYC1-ROBOTICS` |
| Web UI | `http://10.14.19.160` |
| API docs page | `http://10.14.19.160/api` (after UI login) |
| REST base | `http://10.14.19.160/api/v2.0.0` |
| Ports | **80** works; HTTPS `:443` did not connect from lab Mac; `:8080` → 404 |
| Hotspot hostname | `mir.com` (only on MiR’s own Wi‑Fi) |

Do **not** set gateway to `10.14.19.160` or leave office gateway as `192.168.12.1` (MiR internal; reserves `192.168.12.x`). Whether office SSID has general internet: not confirmed.

### Auth / config

- Same username/password as the MiR web UI, stored only in **`.env`** (`MIR_USERNAME` / `MIR_PASSWORD`).
- API Basic auth is `base64(username:sha256_hex(password))` — **not** the plain password. Implemented in `mir/client.py`; do not reimplement in CLI/GUI.
- SHA-256 hash is **case-sensitive**; web UI login may not be. `MirClient` retries entered / lower / upper password hashes on 401.
- Headers: `Content-Type: application/json`, `Accept-Language: en_US`, plus Basic auth.
- `load_dotenv` **overwrites** process env from `.env`.
- Committed example: `.env.example`. Local: `.env` (gitignored). No `config.json` for this device.

### Paths (this device)

| Path | Role |
| --- | --- |
| `mir_command.py` | CLI entry |
| `mir/client.py` | Shared REST client (`MirClient`) |
| `mir/parser.py` | CLI verb parsing / catalogs |
| `gui/` | Thin tkinter GUI (`python -m gui`) |
| `run_cli.*` / `run_gui.*` | Launchers (use project `.venv`) |
| `.env.example` / `.env` | Host + credentials |
| `docs/` | Setup, User Guide, Automation |
| `scripts/` | OS setup entrypoints |
| `tests/` | Unit tests (no robot required) |
| `MIR_HANDOFF.md` | This file |

---

## Software / API (diagnosis)

- API: **v2.0.0** (`API-Version`); product `MiR-Product: MIR200`
- Transport: REST + JSON over **HTTP** at the REST base above
- State IDs: Ready **3**, Pause **4**, Executing **5**, Emergency stop **10**, Error **12** (failed GoTo shows `state_text=Error` plus `errors[]`)
- Prefer positions/missions over joystick velocity commands

### Endpoints in use

| Method | Path | Notes |
| --- | --- | --- |
| GET | `/status` | Works without auth |
| PUT | `/status` | `{"state_id": 3\|4}` Ready / Pause; `{"clear_error": true}` clears software Error (12) |
| GET | `/positions` | Auth; named markers |
| GET | `/missions` | Auth; named missions |
| GET | `/mission_groups` | Needed to create GoTo helper mission |
| GET | `/actions/move` | Optional; shapes move-action parameters |
| POST | `/missions`, POST\|PUT `/missions/{guid}/actions` | Helper move mission |
| POST | `/mission_queue` | `{"mission_id": "<guid>", "priority": 0}` (+ optional `message`) |
| GET | `/mission_queue` | Collection (paginated); many historical Done/Aborted rows |
| GET | `/mission_queue/{id}` | Detail: `state`, `finished`, `message`, `mission_id`, … |
| DELETE | `/mission_queue/{id}` | Abort/remove that queue entry |
| GET | `/paths` | Cached planner paths between positions |
| DELETE | `/paths/{guid}` | Delete one stored path; GUI **Clear paths** deletes all |

### `GET /status` fields (confirmed live 2026-08-13)

| Field | Notes |
| --- | --- |
| `robot_name`, `robot_model`, `serial_number` | Identity |
| `battery_percentage` | float |
| `battery_time_remaining` | **seconds** (int) → format as `H:MM` via `format_battery_time` |
| `state_id` / `state_text` | 3 Ready, 4 Pause, 5 Executing, 10 Emergency stop, 12 Error |
| `mission_text` | Human string (may say Charging… or helper name) |
| `mission_queue_id` / `mission_queue_url` | Active queue entry |
| `map_id` | Current map |
| `position` | `{x, y, orientation}` |
| `distance_to_next_target` | meters — hook for future progress % |
| `errors` | list of `{code, description, module}`; description may be JSON with printf-style `message`/`args`. Surface via `format_robot_errors` when non-empty or state is 10/12 |

Helpers in `mir/client.py`: `format_status`, `format_battery_time`, `format_robot_errors`, `format_estop_details`, `is_terminal_queue_state`, `is_charge_action_name`, `clear_paths`.

### Mission queue / Charge behavior

- After `POST /mission_queue`, poll `GET /mission_queue/{id}` until terminal `state` (`Done`, `Aborted`, `Error`, …) or `finished` is set.
- **Charge is indefinite on the robot.** GUI/scripts never wait for Charge → `Done`.
  - Wait until charging **initiated** (`is_charging_started`: **Docked (8)** or `mission_text` starting with `Charging` — **not** Docking (9) or `Moving to 'Charger'`).
  - If more draft items follow → send next command (interrupts Charge).
  - If Charge is last → end sequence and **leave Charge running** (no abort/pause/ensure_ready).
- **Stop / close / Ctrl-C while charging:** if charging or about to charge, prompt Keep Charging vs Stop Charging; otherwise Stop aborts, window close / Ctrl-C detaches without abort.
- **No re-queue on wait errors:** if already `POST`ed, retry the *wait* only — never double-POST (especially Charge).
- **Stage2Rally** includes moves to **Stage-In** then **Rally** (Mission Status may show `Moving to 'Rally'` while draft item is still `Mission: Stage2Rally`). **RallyToSt2** → **Station 2**. **Charge** → **Charger**, dock, charge action.

### GoToPosition implementation

- Client creates/reuses mission **`CLI_GoToPosition`** with one **`move`** action (position GUID updated), then queues it.
- Helper mission excluded from `get_missions()` listings.
- Queue `message` is set to `GoToPosition <name>` / `RunMission <name>` so Mission Status can show intent when `mission_text` is generic.

---

## Code layout (for agents extending or debugging)

| Path | Role |
| --- | --- |
| `mir_command.py` | CLI entry |
| `mir/client.py` | Auth, status, catalogs, go_to / run_mission, queue CRUD, pause/resume/abort, format helpers, HTTP retries |
| `mir/parser.py` | CLI verb parsing (GUI uses dropdowns, not this) |
| `gui/app.py` | Tk main window; wires panels ↔ services |
| `gui/models.py` | `QueueAction`, `ActionKind`, `RunnerState` |
| `gui/services/draft_queue.py` | Local draft list |
| `gui/services/runner.py` | Sequential Start / Pause / Stop worker |
| `gui/services/status_poller.py` | Periodic `GET /status` |
| `gui/panels/status_panel.py` | Mission Status + Robot Status |
| `gui/panels/catalog_panel.py` | Position / Mission dropdowns + Add |
| `gui/panels/queue_panel.py` | Draft list, reorder, Start/Pause/Stop |
| `gui/panels/map_panel.py` | Stub — open robot UI in browser |
| `tests/` | Parser, GUI helpers, client retries (no robot) |

**Rule:** GUI/CLI stay thin; robot logic stays in `mir/`. Prefer extending `mir/client.py` over reimplementing auth/API in CLI/GUI.

### MirClient methods the GUI relies on

- `from_env()` → `connect()`
- `get_status()`, `get_positions()`, `get_missions()`
- `go_to_position_by_name(..., raise_on_estop=False)` / `run_mission_by_name(..., raise_on_estop=False)`
- `ensure_ready(raise_on_estop=True)` — CLI default **True**; GUI Start uses **False**
- `pause_robot()` / `resume_robot()`; `get_mission_queue_item` / `delete_mission_queue_item` / `abort_active_mission`
- `get_paths()` / `clear_paths()`; `format_robot_errors`; `can_clear_error` (state **12** only); `clear_error()`

### GUI extension map

| Change | Where |
| --- | --- |
| New status field / progress % | `status_panel.py` + optional `format_*` in `mir/client.py`; use `distance_to_next_target` |
| Clear paths / clear Error | Already wired via `MirClient` |
| New control button | Add `MirClient` method → `app.py` / `queue_panel.py` |
| Send whole draft at once | `gui/services/runner.py` (`QueueRunner._run_loop`) |
| Map embed | Replace `gui/panels/map_panel.py` |
| Block Start on e-stop / confirm | `app.py` `_start` / `QueueRunner.start` (today permissive) |
| Charger leave warning | CLI has it; GUI deliberately omitted |
| Look & feel | ttk in `app.py` / panels only |

### Runner / HTTP semantics (v1)

- Draft is local until Start; Start pops from front as each item is sent.
- After each queue entry reaches terminal state, runner immediately sends the next item (empty draft / Pause / Stop / hard API error ends the run).
- After Aborted/Error, robot often enters state **12** — runner calls `clear_error` / `ensure_ready` before the next item (otherwise sequence looked like it “stopped after the first action”).
- `MirClient.request` uses `threading.RLock` so poller + runner share one session.
- **Timeouts:** connect 15s / read 60s default; override with `.env` `MIR_CONNECT_TIMEOUT`, `MIR_READ_TIMEOUT`, or `MIR_HTTP_TIMEOUT`.
- **Retries (2026-09-17):** default 3 with backoff via `MIR_HTTP_RETRIES` / `MIR_HTTP_RETRY_BACKOFF`. Connect/reset → retry any method; read timeout or 5xx/429 → retry **GET/HEAD only** (never auto-retry `POST /mission_queue` after read timeout — could double-queue Charge). Set `MIR_HTTP_RETRIES=0` to disable. Helpers: `should_retry_mir_request`, `is_transient_mir_error`; tests in `tests/test_client_retries.py`.

---

## Safety / battery (API cannot override BMS)

- REST talks to MiR software only — **not** the battery pack BMS.
- **Physical e-stop (10):** clear on the robot; API cannot clear it.
- **Software Error (12):** `PUT /status {"clear_error": true}` via GUI **Clear errors** / `ensure_ready` — for recoverable software faults, **not** BMS override. Do not auto-loop `clear_error` to ignore battery faults.
- **Docked / cable charging:** if BMS still trips, treat as battery/service issue. Capture `status.errors` from Robot Status / `Status` command.

Ask before any motion command or GUI Start.

---

## Migration notes

| Date | Change |
| --- | --- |
| 2026-09-30 | Copied `~/Desktop/MiR_API` → `~/Documents/PyControl/devices/MiR_API` (on WS-RHCV7HYY6K). User chose copy-first. Added tagged docs + setup scripts; `.env` copied locally for smoke test. |
| 2026-09-30 | User confirmed `Status` from new path. Renamed `~/Desktop/MiR_API` → `~/Desktop/MiR_API_backup_20260930` (on WS-RHCV7HYY6K). |
| 2026-09-30 | Merged `docs/PROJECT_KNOWLEDGE.md` into this handoff; deleted duplicate. |

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
| `PAI_Lab` | `PAI_Lab_Backup_Handoff.md` | Retired hub — local-only backup `PyControl/backups/PAI_Lab_backup_20261001/` (gitignored; on WS-RHCV7HYY6K) |

H1 code was removed from this MiR tree on 2026-09-08; H1 demo later lived in `H1_Lab` (2026-09-14).

---

## Quick verify

```bash
cd /path/to/PyControl/devices/MiR_API
./run_cli.sh Status
# or: source .venv/bin/activate && python mir_command.py Status
```

Expect robot name **MiR_S1169** and IP **10.14.19.160** (unless the network changed — update this handoff if so). Everyday use: [docs/MIR_USER_GUIDE.md](docs/MIR_USER_GUIDE.md). Agents setting up: [docs/MIR_AUTOMATION.md](docs/MIR_AUTOMATION.md).

---

## Guardrails / gotchas

- Ask before any motion command or GUI Start.
- Never commit `.env` / passwords / auth headers / Basic-auth strings.
- Plain-password Basic auth → **401**; always SHA-256 hex the password.
- Password capitalization mismatches UI vs API were a real failure mode; client retries case variants.
- **Privacy (per `ALIGNMENT_HANDOFF.md`):** `docs/MIR_SETUP.md` / `docs/MIR_AUTOMATION.md` contain no real usernames. This handoff may hold real names, serials, IPs, and accurate paths — but **never secrets**.
- Prefer extending `mir/client.py` over reimplementing auth in CLI/GUI.
- GUI toolkit v1 = **tkinter** (no extra dependency).
- GUI does not raise on e-stop when queueing (`raise_on_estop=False`); robot may still reject the command.
