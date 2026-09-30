# MiR API — project knowledge

Last updated: 2026-09-30

Source: chats “MiR200 API interface”, “Network section update”, “MiR command script design”, and “MiR GUI” (2026-08-11 → 2026-08-13). Live HTTP probes against the robot confirmed connectivity, auth, and status fields used by the GUI.

**Lab instruments:**
- **H1-only control/GUI:** `PyControl/devices/H1_Lab` (see its `H1_HANDOFF.md` and `docs/H1_SETUP.md`).
- **Multi-device lab hub:** `~/Documents/PAI_Lab` (`lab_device_control.py`, `lab/`).
- H1 code was removed from this MiR_API tree on 2026-09-08 so this repo stays MiR200-only. H1 demo CLI/GUI later split to `H1_Lab` on 2026-09-14.
- **Canonical MiR path (2026-09-30):** `PyControl/devices/MiR_API/` — durable robot facts live in **`MIR_HANDOFF.md`**.

## Documentation map

| Doc | Role |
|-----|------|
| [MIR_README.md](../MIR_README.md) | Project overview and quick start |
| [MIR_SETUP.md](MIR_SETUP.md) | Human install (Mac / Windows / Linux) |
| [MIR_USER_GUIDE.md](MIR_USER_GUIDE.md) | Everyday CLI / GUI usage |
| [MIR_AUTOMATION.md](MIR_AUTOMATION.md) | Agent setup playbook (no secrets in chat) |
| [MiR_AUTOSETUP.md](MiR_AUTOSETUP.md) | Legacy stub → points at MIR_AUTOMATION.md |
| [`../MIR_HANDOFF.md`](../MIR_HANDOFF.md) | Progress, network, smoke test, undo |

**Standard install path:** `PyControl/devices/MiR_API/` (preferred root from machine handoff / `~/PyControl`).  
**Launchers:** `run_cli.sh` / `run_gui.sh` (Windows: `run_cli.bat` / `run_gui.bat`), or activate `.venv` and run `mir_command.py` / `python -m gui`.

Prefer pointing new machines / new agents at **MIR_AUTOMATION.md**; humans use **MIR_SETUP.md** then **MIR_USER_GUIDE.md**.

## Product intent (what the user wants)

- Command the MiR200 from this computer over the native REST API, while also using the full robot web UI on office WiFi (not stuck on the MiR hotspot).
- **Working today:**
  - Terminal console: `mir_command.py`
  - Desktop GUI: `python -m gui` (tkinter; thin UI over `MirClient`)
- Prefer extending `mir/client.py` (+ helpers) rather than re-implementing API/auth in CLI/GUI.
- CLI command UX (unchanged unless the user changes it):
  - `GoToPosition <name>`, `RunMission <name>`, typo correction, live catalogs from the robot.
- GUI UX (v1 decisions):
  - Separate **Position** and **Mission** dropdowns (not one mixed list).
  - **Draft** action queue with Add / Remove / Clear / ▲▼ / drag-and-drop reorder.
  - **Start** runs the draft **continuously** one item at a time: the GUI waits for each robot queue entry to finish before sending the next. **Charge** is indefinite on the robot — the GUI waits only until charging has *initiated*, then either ends (if Charge is last) or sends the next draft action (which interrupts Charge).
  - **Pause** / **Stop** control the runner + robot; **Clear paths** deletes stored planner paths; **Clear errors** is enabled only in software Error state (12).
  - No confirm dialog on Start; do **not** block queueing on e-stop; no charger leave warning in GUI.
  - Mission Status + Robot Status readouts (including Error state details from `status.errors`); map embedding deferred (browser button stub only).
  - Progress % / distance estimate deferred (easy later via `distance_to_next_target`).
  - Look & feel is intentionally simple for now.

## Fleet / hardware

- Robot name: MiR_S1169
- Model: MiR200
- Serial: 190200015001169
- Ethernet: not available at this site (WiFi only)
- Charging: floor dock (**Charge** mission) and rear **cable charger** (OEM 24 VDC 10 A + rocker switch). Cable charging is for a **powered-off** robot. Plug in or flip the charge switch and the robot goes to **emergency stop** by design (MiR200 user/quick-start). It is not a laptop-style AC adapter: the PC still runs from the pack; the wall brick charges through the BMS.
- Observed 2026-08-18: robot still **fully powers off** while on the wall outlet with the battery/charge switch in wired-charging mode. Treat as BMS pack disconnect, not an API/GUI keep-alive problem.

## Network

- Robot IP: `10.14.19.160` (treat as current unless it changes)
- Office WiFi SSID: `OPTRN-NYC1-ROBOTICS`
- Full robot UI: `http://10.14.19.160` (HTTP works)
- API docs page: `http://10.14.19.160/api` (launch docs from the UI after login)
- REST base URL: `http://10.14.19.160/api/v2.0.0` (confirmed)
- Ports: **80 works**. HTTPS `:443` did not connect from this laptop. `:8080` returned 404.
- Robot hotspot hostname: `mir.com` (only on the MiR’s own WiFi)
- Do **not** set gateway to `10.14.19.160` or leave office gateway as `192.168.12.1` (MiR internal). MiR reserves `192.168.12.x` internally.
- Whether `OPTRN-NYC1-ROBOTICS` has general internet: not confirmed.

## Software / API facts

- MiR software: **2.13.1.4** (`Robot-Version` header)
- API: **v2.0.0** (`API-Version`); product `MiR-Product: MIR200`
- Transport: REST + JSON over **HTTP** at `http://10.14.19.160/api/v2.0.0`
- Auth (critical):
  - Same username/password as the MiR web UI (stored only in `.env` as `MIR_USERNAME` / `MIR_PASSWORD` — never commit or put secrets in this file).
  - API Basic auth is **`base64(username:sha256_hex(password))`**, not the plain password.
  - Web UI login can be case-insensitive; the SHA-256 hash is **case-sensitive**. `MirClient` tries entered / lower / upper password hashes on 401.
  - Implemented in `mir/client.py`. GUI/CLI must use `MirClient`, not roll their own auth.
- Headers: `Content-Type: application/json`, `Accept-Language: en_US`, plus Basic auth as above.
- State IDs: Ready **3**, Pause **4**, Executing **5**, Emergency stop **10**, Error **12** (confirmed live: failed GoTo shows `state_text=Error` plus `errors[]`).
- Prefer positions/missions over joystick velocity commands.

### Endpoints in use

| Method | Path | Notes |
|--------|------|--------|
| GET | `/status` | Works without auth. See status fields below. |
| PUT | `/status` | `{"state_id": 3\|4}` Ready / Pause; `{"clear_error": true}` clears software Error (12) |
| GET | `/positions` | Auth; named markers |
| GET | `/missions` | Auth; named missions |
| GET | `/mission_groups` | Needed to create GoTo helper mission |
| GET | `/actions/move` | Optional; shapes move-action parameters |
| POST | `/missions`, POST\|PUT `/missions/{guid}/actions` | Helper move mission |
| POST | `/mission_queue` | `{"mission_id": "<guid>", "priority": 0}` (+ optional `message`) |
| GET | `/mission_queue` | Collection (paginated); many historical Done/Aborted rows |
| GET | `/mission_queue/{id}` | Detail: `state`, `finished`, `message`, `mission_id`, … |
| DELETE | `/mission_queue/{id}` | Abort/remove that queue entry (`allowed_methods` includes DELETE) |
| GET | `/paths` | Cached planner paths between positions |
| DELETE | `/paths/{guid}` | Delete one stored path (`allowed_methods` includes DELETE). GUI **Clear paths** deletes all. |

### `GET /status` fields confirmed live (2026-08-13)

Useful for GUI (non-exhaustive):

| Field | Example / notes |
|-------|-----------------|
| `robot_name`, `robot_model`, `serial_number` | Identity |
| `battery_percentage` | float, e.g. `100.0` |
| `battery_time_remaining` | **seconds** (int), e.g. `47999` → format as `H:MM` via `format_battery_time` |
| `state_id` / `state_text` | 3 Ready, 4 Pause, 5 Executing, 10 Emergency stop |
| `mission_text` | Human string from robot (may say Charging… or helper name) |
| `mission_queue_id` / `mission_queue_url` | Active queue entry id |
| `map_id` | Current map |
| `position` | `{x, y, orientation}` |
| `distance_to_next_target` | float meters — **hook for future progress %** (not shown in GUI v1) |
| `errors` | list of `{code, description, module}`; description may be a JSON string with `message` + `args` (printf-style). Always surface via `format_robot_errors` when non-empty or state is 10/12. |
| `velocity`, `mode_text`, `uptime`, … | Available if needed later |

Helpers in `mir/client.py`: `format_status`, `format_battery_time`, `format_robot_errors`, `format_estop_details`, `is_terminal_queue_state`, `is_charge_action_name`, `clear_paths`.

### Mission queue completion

- After `POST /mission_queue`, poll `GET /mission_queue/{id}` until `state` is terminal (`Done`, `Aborted`, `Error`, …) or `finished` is set.
- **Charge (indefinite on robot):** the GUI/script never waits for Charge to reach `Done`.
  - Always wait until charging has **initiated** (`is_charging_started`).
  - If more draft items follow → then send the next command (interrupts Charge on the robot).
  - If Charge is last → end the GUI sequence and **leave the Charge mission running** (no abort/pause/ensure_ready). Only a later **Start** with new actions (or Stop *during* a run) may interrupt Charge.
- **Charge wait signal:** `is_charging_started` is true for **Docked (8)** or `mission_text` starting with `Charging` — **not** for Docking (9) or `Moving to 'Charger'`. Early “started” detection used to abort Charge mid-dock when the next draft item was sent.
- **Stop / close / Ctrl-C while charging:** if the robot is charging or about to charge (docking / moving to Charger on a Charge mission), show a dialog: headline “MiR is charging” or “MiR is about to charge”, question “Do you want to stop charging?”, buttons **Keep Charging** (detach — leave mission running) and **Stop Charging** (abort active mission). If not in a charge path: **Stop** aborts active missions; window close / Ctrl-C only detaches (does not abort).
- **No re-queue on wait errors:** if a mission was already `POST`ed, errors retry the *wait* only — never POST the same action twice.
- **Stage2Rally** includes moves to **Stage-In** then **Rally**. Mission Status may show `Moving to 'Rally'` while the draft item is still `Mission: Stage2Rally` — that is not a separate GoTo in the draft.
- **RallyToSt2** moves to **Station 2**. **Charge** moves to **Charger**, docks, then runs the charging action.

## Code layout

Cursor always-apply rule: `.cursor/rules/architecture.mdc` — GUI/CLI stay thin; robot logic stays in `mir/`.

| Path | Role |
|------|------|
| `mir_command.py` | CLI entry (keep working). |
| `mir/client.py` | `MirClient`: auth, status, catalogs, go_to / run_mission, queue CRUD, pause/resume/abort, status format helpers. |
| `mir/parser.py` | CLI verb parsing / catalogs (GUI does not need this for dropdowns). |
| `gui/` | Desktop GUI package (`python -m gui`). |
| `gui/app.py` | Tk main window; wires panels ↔ services. |
| `gui/models.py` | `QueueAction`, `ActionKind`, `RunnerState`. |
| `gui/services/draft_queue.py` | Local draft list (not robot queue until Start). |
| `gui/services/runner.py` | Sequential Start / Pause / Stop worker thread. |
| `gui/services/status_poller.py` | Periodic `GET /status` for readouts. |
| `gui/panels/status_panel.py` | Mission Status + Robot Status. |
| `gui/panels/catalog_panel.py` | Position / Mission dropdowns + Add. |
| `gui/panels/queue_panel.py` | Draft list, reorder, Start/Pause/Stop. |
| `gui/panels/map_panel.py` | **Stub** — “Open robot UI in browser”; replace later for embed. |
| `tests/test_parser.py` | Parser unit tests |
| `tests/test_gui_helpers.py` | Draft queue + status helper unit tests (no robot) |
| `.env` / `.env.example` | Secrets and host (MiR only) |
| `requirements.txt` | `requests` (GUI uses stdlib `tkinter`) |
| `.venv/` | Local virtualenv |

### MirClient methods the GUI relies on

- `from_env()` → `connect()`
- `get_status()`, `get_positions()`, `get_missions()`
- `go_to_position_by_name(..., raise_on_estop=False)` / `run_mission_by_name(..., raise_on_estop=False)`
- `ensure_ready(raise_on_estop=True)` — CLI default **True**; GUI Start uses **False**
- `pause_robot()` → PUT state 4; `resume_robot()` → PUT state 3
- `get_mission_queue_item(id)`, `delete_mission_queue_item(id)`, `abort_active_mission()`
- `get_paths()`, `clear_paths()` — delete all cached planner paths
- `format_robot_errors(status)` — Error/e-stop/`errors[]` readout
- `can_clear_error(status)` — True only for state_id **12**
- `clear_error()` — `PUT /status {"clear_error": true}` (raises if not clearable)

### GoToPosition implementation detail

- Client creates/reuses mission **`CLI_GoToPosition`** with one **`move`** action (position GUID updated), then queues it.
- Helper mission excluded from `get_missions()` listings.
- Queue `message` is set to `GoToPosition <name>` / `RunMission <name>` so Mission Status can show intent even when robot `mission_text` is generic.

## How to run

Full cross-OS instructions: [MIR_USER_GUIDE.md](MIR_USER_GUIDE.md). Agent automation: [MIR_AUTOMATION.md](MIR_AUTOMATION.md).

**Standard path:** `PyControl/devices/MiR_API/` (preferred root from machine handoff / `~/PyControl`).

```bash
cd ~/Documents/PyControl/devices/MiR_API   # or your machine-handoff PyControl path
# .env must contain MIR_USERNAME / MIR_PASSWORD

# Supported launchers (preferred)
./run_cli.sh              # CLI (Windows: run_cli.bat)
./run_cli.sh Status
./run_gui.sh              # GUI (Windows: run_gui.bat)

# Tests (no robot required)
.venv/bin/python -m unittest discover -s tests
```

Do **not** run `.venv/bin/activate` as a program; use `source .venv/bin/activate` (or Windows `.\.venv\Scripts\Activate.ps1`) only if needed. Day-to-day use should be `run_cli` / `run_gui` from the PyControl device folder.

## GUI extension guide (for future chats)

Keep panels dumb; put robot/IO behavior in `mir/` or `gui/services/`.

| Change | Where to edit |
|--------|----------------|
| New status field / progress % | `status_panel.py` + optionally `format_*` in `mir/client.py`; poller already feeds full status. Use `distance_to_next_target` + start distance for %. |
| Clear stored planner paths | `MirClient.clear_paths()` — already wired to GUI **Clear paths**. |
| Clear software Error | `MirClient.clear_error()` / `can_clear_error()` — GUI **Clear errors** (enabled only in state 12). |
| New control button (e.g. Clear robot queue) | Add `MirClient` method → wire in `app.py` / `queue_panel.py`. |
| Send whole draft chain at once | `gui/services/runner.py` (`QueueRunner._run_loop`) — replace wait-between-items with multiple POSTs. |
| Map embed / map image | Replace `gui/panels/map_panel.py`; `app.py` already packs it. |
| Different toolkit (Qt, web) | Reuse `gui/models.py` + `gui/services/*` + `MirClient`; rewrite panels only. |
| Block Start on e-stop / confirm dialog | `app.py` `_start` / `QueueRunner.start` (today intentionally permissive). |
| Charger leave warning | CLI has it in `mir_command.py`; GUI deliberately omitted. |
| Look & feel | ttk themes / styles in `app.py` / panels only. |

### Runner semantics (v1)

- **Draft queue** is local until Start; Start pops from the front as each item is sent.
- **Start runs the full remaining draft continuously**: after each mission_queue entry reaches a terminal state (`Done` / `Aborted` / …), the runner immediately sends the next draft item. It does **not** stop between items; only an empty draft, **Pause**, **Stop**, or a hard API error ends the run.
- After **Aborted/Error** queue results the robot often enters state **12**. The runner calls `clear_error` / `ensure_ready` before the next item (and `ensure_ready` itself clears state 12). Otherwise the sequence looked like it “stopped after the first action.”
- **Charge:** GUI waits until charging *initiated*, not until Charge finishes. If more draft items follow, GUI then sends the next action (interrupts Charge). If Charge is last, GUI ends with `_preserve_charging` and does **not** abort/pause the mission (Stop while Idle also leaves Charge alone). A later Start with new actions clears that flag and may interrupt Charge.
- Draft items are removed only after that item was handled successfully (failed sends stay in the draft).
- **Clear paths:** deletes every `GET /paths` entry via `DELETE /paths/{guid}` so the planner can replan.
- **Clear errors:** GUI button enabled only when `can_clear_error(status)` (state **12**). Calls `MirClient.clear_error()` → `PUT /status {"clear_error": true}`. E-stop (**10**) stays disabled — must be cleared on the robot.
- **Error readout:** Robot Status shows `format_robot_errors` for state Error (12), e-stop (10), or any non-empty `errors` (expands JSON `description` templates).
- **Start** while paused → Resume (sets Ready + continues the same run).
- **Pause** → local pause event + `pause_robot()` (blocks before/during wait; Start resumes).
- **Stop** → abort runner + `abort_active_mission()` (DELETE active queue id + Pause).
- `MirClient.request` is locked (`threading.RLock`) so the status poller and queue runner can share one session safely.
- **HTTP timeouts (CLI + GUI share `MirClient`):** default **connect 15s / read 60s** (was a flat 12s, discovery 5s). Override with `.env` `MIR_CONNECT_TIMEOUT`, `MIR_READ_TIMEOUT`, or `MIR_HTTP_TIMEOUT` (sets both). Raise read timeout if polls fail while the robot is busy between draft steps.
- **HTTP retries (2026-09-17, CLI + GUI via `MirClient.request`):** default **3 retries** with backoff `MIR_HTTP_RETRY_BACKOFF * attempt` (default 1s, 2s, 3s). Tunable via `.env` `MIR_HTTP_RETRIES` / `MIR_HTTP_RETRY_BACKOFF`.
  - **Safe policy:** connect / connection-reset style transport errors → retry **any** method (request likely never reached the robot). **Read timeout** or HTTP 5xx/429 → retry **GET/HEAD only** — never auto-retry `POST /mission_queue` after a read timeout (could double-queue Charge).
  - **Why:** intermittent WiFi (metal load over antenna, map dead spots) often fails *between* draft steps after a move completes; hardening belongs in `mir/client.py`, not GUI-only.
  - **Revert:** set `MIR_HTTP_RETRIES=0` in `.env` and restart CLI/GUI; or remove the retry loop in `MirClient.request` / helpers `should_retry_mir_request`, `_http_retries_from_env`.
  - Related helpers: `is_transient_mir_error`, `should_retry_mir_request` in `mir/client.py`; tests in `tests/test_client_retries.py`.

## Safety / battery (API cannot override BMS)

The REST client talks to MiR software (`GET`/`PUT /status`, mission queue). It does **not** talk to the battery pack BMS.

- **BMS power cut / robot PC reboot:** hardware protection. Scripts and GUI cannot keep the robot alive; a dead-man’s switch on this laptop cannot either.
- **Physical e-stop (state 10):** must be cleared on the robot. API will not clear it.
- **Software Error (state 12):** `PUT /status {"clear_error": true}` — already in GUI **Clear errors** / `ensure_ready`. This is for recoverable software faults (failed GoTo, etc.), **not** a BMS override. Do not auto-loop `clear_error` to ignore battery faults.
- **Docked charging:** the supported “stay on wall power” path is the **Charge** mission (already treated as indefinite). If the BMS still trips while docked, that is a battery/service issue, not something this repo can patch around.
- **Cable / wall charging:** same story. The rear charger does not independently power the robot PC. MiR documents recommend turning the robot **off** during cable charge; cable or charge-switch on → e-stop. Site observation: it still **shuts off completely** in that mode, so a GUI dead-man cannot keep it up.

If a battery fault is interrupting work, capture `status.errors` (code, module, description) from Robot Status / `mir_command.py Status` and treat replacement or MiR service as the fix.

## Procedures (short)

1. Ensure the project is at `PyControl/devices/MiR_API/` (see machine handoff for PyControl root).
2. Join WiFi `OPTRN-NYC1-ROBOTICS` → open `http://10.14.19.160` → confirm UI.
3. Ensure `.env` in the device folder has UI credentials.
4. CLI: `./run_cli.sh` (or `run_cli.bat`) — safe tests `Status`, `ListPositions`, `ListMissions`.
5. GUI: `./run_gui.sh` (or `run_gui.bat`) — refresh lists, build draft, Start only when area is clear.
6. Real motion only when the area is clear.

## Decisions and gotchas

- Goal: local control via REST + full web UI on facility WiFi.
- Plain-password Basic auth → **401**; always SHA-256 hex the password for API auth.
- Password capitalization mismatches UI vs API were a real failure mode; client retries case variants.
- `load_dotenv` **overwrites** process env from `.env`.
- Do not store passwords, tokens, or Basic-auth strings in this file.
- GUI toolkit v1 = **tkinter** (no extra dependency). Map live-embed skipped; browser open is enough for now.
- CLI still warns on charging; GUI does not (per product decision 2026-08-13).
- GUI does not raise on e-stop when queueing (`raise_on_estop=False`); robot may still reject the command.
