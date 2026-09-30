# H1_HANDOFF — BioTek Synergy H1

Living device brief for the **BioTek Synergy H1** under the shared **PyControl** layout.  
**Update this file whenever objectives, progress, or durable facts change.**

Filename convention: device handoffs are `<TAG>_HANDOFF.md` (this file = `H1_HANDOFF.md`). See repo-root `ALIGNMENT_HANDOFF.md`.

---

## How to update this document

1. Read at session start.
2. Edit before ending work that changes goals, status, config, or next steps.
3. Keep concise; prefer bullets.
4. Do not delete durable facts unless proven wrong — replace with a dated correction.
5. Set **Last updated** to today when you change Progress or Durable details.
6. Secrets stay in local config / env — not here.
7. If docs/scripts/CLI behavior change, also update `H1_README.md`, `docs/H1_SETUP.md`, `docs/H1_USER_GUIDE.md`, `docs/H1_AUTOMATION.md`, and repo-root [`ALIGNMENT_HANDOFF.md`](../../ALIGNMENT_HANDOFF.md) if the shared pattern changed.

---

## Last updated

2026-09-30 — Renamed everyday docs to tagged names (`H1_README.md`, `docs/H1_SETUP.md`, `docs/H1_USER_GUIDE.md`, `docs/H1_AUTOMATION.md`); no bare README stub. — Jesse Martin (via agent) on WS-RHCV7HYY6K

Earlier 2026-09-30 — Renamed `HANDOFF.md` → `H1_HANDOFF.md` per PyControl naming convention (Flex alignment pass). Old `~/Documents/H1_Lab` renamed to `~/Documents/H1_Lab_backup_20260929`; references repointed. **H1 migration complete.** Longevity pass: removed `PAI_Lab` H1 redirect stubs; replaced real usernames with `~` / `<username>`; standardized undo steps; added backup-deletion checklist and smoke test. Adopted Flex privacy norm (handoffs keep real facts + attribution; no secrets). — Jesse Martin (via agent) on WS-RHCV7HYY6K

---

## Objectives

### In scope

Reliable Python control layer (`h1_control.py`) + thin GUI (`h1_gui.py`) so humans or a PAI can choreograph H1 demo steps over USB: tray open/close, status, absorbance → CSV+JSON. Cross-platform. Easy setup. Choreography reliability > research-grade assays.

### Out of scope (guide only)

Multi-device hub/gateway (lives in `PAI_Lab`), public-internet control, research assay validation, installer/Docker/systemd packaging.

---

## Progress

| Status | Item |
| --- | --- |
| Done | CLI: open/close/cycle/status/absorbance (`--repeats`, `--no-prompt`, `--already-loaded`) |
| Done | GUI (tkinter, subprocess CLI only) — user-verified pre-migration |
| Done | Absorbance @ 600 nm + repeatability — user-verified pre-migration |
| Done | PyControl layout: `devices/H1_Lab/` |
| Done | `config.example.json` / `config.json` (`.env` fallback kept); `results/` output dir |
| Done | `discover` command (`--set-device-id`, `--save`) |
| Done | GUI picks `.venv` Python on Windows (`Scripts\python.exe`) |
| Done | `scripts/setup_mac.sh`, `setup_linux.sh`, `setup_windows.ps1` |
| Done | `docs/H1_SETUP.md`, `docs/H1_USER_GUIDE.md`, `docs/H1_AUTOMATION.md`, `H1_README.md` (tagged names) |
| Done | User ran `setup_mac.sh` → `SETUP OK` (`status` from new path) |
| Done | Repointed `PAI_Lab` stubs/docs, `MiR_API/docs/PROJECT_KNOWLEDGE.md`, PyControl README, Flex HANDOFF |
| Done | Git ignore verified: `config.json` and `.venv` excluded (`git check-ignore`) |
| Done | Tray `open` → `close` from new path (user-verified 2026-09-29) |
| Done | Git commit `449ab4f` (H1_Lab + root README/.gitignore; Flex files left for Flex chat) |
| Done | Device handoff renamed to `H1_HANDOFF.md` |
| Done | Old `~/Documents/H1_Lab` renamed to `~/Documents/H1_Lab_backup_20260929` (kept as backup; nothing deleted) |
| Done | Cursor workspace for this work moved to `~/Documents/PyControl` |
| Done | Deleted `PAI_Lab` redirect stubs (`h1_control.py`, `h1_gui.py`, `h1_absorbance_test.py`, `PAI_Lab_Cursor_PyLabRobot_Handoff_concise_v3.md`) — 2026-09-30 |
| Done | Real usernames removed from H1/PyControl/PAI_Lab/backup text docs (`~` / `<username>` convention) |
| Done | Smoke test / Undo / Before-you-delete-backup generalized into `ALIGNMENT_HANDOFF.md` (rule + done-checklist item) and `templates/DEVICE_HANDOFF.md` (blank sections); this file is the reference example |
| Done | Smoke test steps 1–4 passed after the 2026-09-30 cleanup (discover, status, open, close) — Jesse Martin on WS-RHCV7HYY6K |
| Pending | Commit 2026-09-30 H1/Flex/shared-doc edits — user chose to have the MiR alignment chat commit everything once MiR verifies (avoid concurrent-edit conflicts) |
| Pending | GUI smoke from new path (optional; worked pre-migration) |
| Pending | Windows / Linux hardware verification |
| Deferred | `pai_signal` emit from CLI/GUI ("demo contract") |

### Next steps

User decisions (2026-09-29):

1. **Tray test** — yes: guided `open` → `close` from the new path (no GUI). **Passed.**
2. **Git commit** — done as `449ab4f` after the tray test. Uncommitted Flex changes were intentionally left for the Flex chat to commit.
3. **Old `~/Documents/H1_Lab`** — kept as backup, renamed `~/Documents/H1_Lab_backup_20260929` (matches `PAI_Lab_backup_20260908`). Only copy of `.docx` guides, `h1_absorbance_test.py`, old results. Do not delete without explicit confirmation.

Remaining: user runs the **Smoke test** below; optional GUI smoke; Windows/Linux verification; `pai_signal` when requested. MiR_API alignment happens in its own chat (its docs still contain a real username; the MiR agent should apply the no-username rule from `ALIGNMENT_HANDOFF.md`).

Session notes:

- `PAI_Lab` no longer has any H1 redirect stubs (removed 2026-09-30; `PAI_Lab` is not a git repo, so they are not recoverable — they only printed a "moved" message). Stale H1 result files `PAI_Lab/h1_absorbance_600nm_result.*` remain (not redirects; left as-is).
- Git commit metadata (author name/email) still contains the real name; that is standard Git behavior and was not rewritten.
- Backup `.docx` guides were not edited (binary; superseded by `docs/*.md`).
- Backup's `.venv` may not work at the renamed path (venvs store their absolute path). See **Undo** below.

---

## Smoke test (run after any change to code, paths, or setup)

Run from the device folder with `.venv` active. Steps 1–2 are agent-safe; step 3 needs the H1; step 4 moves hardware (**ask first**).

```bash
cd /path/to/PyControl/devices/H1_Lab
source .venv/bin/activate   # Windows: .\.venv\Scripts\Activate.ps1
```

| Step | Command | Pass looks like | Moves? |
| --- | --- | --- | --- |
| 1. Code loads | `python -m py_compile h1_control.py h1_gui.py && python h1_control.py --help` | No errors; usage text lists `open, close, cycle, status, absorbance, discover` | No |
| 2. Scripts parse (Mac/Linux) | `bash -n scripts/setup_mac.sh && bash -n scripts/setup_linux.sh` | No output | No |
| 3a. USB visible | `python h1_control.py discover` | Lists a device ending `:22040106` | No |
| 3b. Instrument talks | `python h1_control.py status` | `Connected to Synergy H1.` / `Serial: 22040106` | No |
| 4. Tray | `python h1_control.py open` then `python h1_control.py close` | `Tray opened.` then `Tray closed.` | **Yes** |

Optional: `python h1_gui.py` → click **Status**. Full re-setup check: `./scripts/setup_mac.sh --non-interactive` → `SETUP OK`.  
Log the result (date + pass/fail) in **Progress**.

---

## Durable details

### Instrument / USB

| Field | Value |
| --- | --- |
| Instrument | BioTek Synergy H1 |
| USB serial (FTDI device id) | `22040106` |
| FTDI VID / PID | `0x0403` / `0x6001` |
| Plate (physical) | Corning Axygen `P-96-450V-C-S` |
| Plate (PyLabRobot) | `Cor_Axy_96_wellplate_500uL_Ub` |
| Demo wavelength | 600 nm |

### Environment (proven Mac)

- Apple Silicon; Python 3.14.5 (python.org framework); PyLabRobot 0.2.2 (`SynergyH1Backend`); `pylibftdi` / `pyusb`
- Homebrew `libftdi` 1.5 + `libusb` 1.0; `DYLD_LIBRARY_PATH` line in `.venv/bin/activate` (setup script adds it)
- Windows: likely needs libusb/libftdi + WinUSB driver (Zadig) — unverified; may conflict with Gen5
- Linux: `libftdi1-2`, udev rule for `0403:6001` — unverified

### Settings precedence

`--device-id` → `H1_FTDIDEVICE_ID` env → `config.json` `ftdi_device_id` → `.env` (only if no `config.json`) → `22040106`.  
`results_dir` (default `results`, relative to device folder). JSON schemas: `h1_lab.absorbance_result.v1`, `h1_lab.absorbance_repeat_summary.v1`.

### Paths (this device)

| Path | Role |
| --- | --- |
| `h1_control.py` | CLI + library |
| `h1_gui.py` | Thin GUI (calls CLI via subprocess; no PyLabRobot import) |
| `config.example.json` | Committed defaults |
| `config.json` | Local settings (gitignored) |
| `results/` | Absorbance output (gitignored except `.gitkeep`) |
| `docs/` | Setup, User, Automation |
| `scripts/` | OS setup entrypoints |
| `H1_HANDOFF.md` | This file |

### Architecture (confirmed 2026-09-14)

1. **Device labs** (`H1_Lab`, `Flex_Lab`, `MiR_API`, future Mantis) — local control + thin GUI; devices don't call each other.
2. **Hub** (`PAI_Lab`, separate folder) — future multi-device gateway / shared vocabulary.
3. **Choreography / PAI** — calls device CLIs in sequence.

Control from: the always-on USB computer; same LAN via RDP into it; remote colleague via RDP into it. Non-RDP LAN / VPN = later (hub). Never expose the instrument on the public internet.

---

## Migration / rename note (read first if paths look wrong)

| Date | Change |
| --- | --- |
| 2026-09-14 | H1 code/docs split out of `PAI_Lab` into `~/Documents/H1_Lab`; schema prefix `pai_lab.h1.*` → `h1_lab.*` |
| 2026-09-29 | Copied into `PyControl/devices/H1_Lab`; `.env` → `config.json`; outputs → `results/`; `requests` dropped from requirements; old docs replaced by `docs/H1_SETUP.md` / `H1_USER_GUIDE.md` / `H1_AUTOMATION.md` |
| 2026-09-30 | `HANDOFF.md` → `H1_HANDOFF.md` |
| 2026-09-30 | Old `~/Documents/H1_Lab` → `~/Documents/H1_Lab_backup_20260929` (on WS-RHCV7HYY6K) |
| 2026-09-30 | `PAI_Lab` H1 redirect stubs deleted; usernames → `~` / `<username>` in docs |

All migration rows above: Jesse Martin (via agent) on WS-RHCV7HYY6K.

Not copied (only in `~/Documents/H1_Lab_backup_20260929`): `.docx` guides, `h1_absorbance_test.py`, old result files, `H1_autosetup.md`, old handoff.

**If something breaks after the move:**

1. `cwd` is `PyControl/devices/H1_Lab`, not the backup folder or `PAI_Lab`.
2. Use this folder's `.venv` (re-run the setup script to rebuild it).
3. Missing serial? `config.json` exists but lacks `ftdi_device_id` → `.env` is ignored once `config.json` exists.
4. There are no H1 scripts in `PAI_Lab` anymore; any `h1_*.py` there is not canonical.
5. Rebuild this folder's venv: delete `.venv`, re-run `scripts/setup_mac.sh` (or the Linux/Windows script).

### Undo (return to the pre-migration project)

Backup convention: a retired copy is renamed `<Folder>_backup_<YYYYMMDD>` in the same parent folder (here `~/Documents/H1_Lab_backup_20260929`, **on WS-RHCV7HYY6K only** — it is not in the zip; on other computers Undo = git history).

1. Rename `~/Documents/H1_Lab_backup_20260929` back to `~/Documents/H1_Lab` (its `.venv` only works at that path).
2. `cd ~/Documents/H1_Lab && .venv/bin/python3 h1_control.py status` (reads its `.env`). If it fails, delete its `.venv` and recreate: `python3 -m venv .venv && .venv/bin/pip install -r requirements.txt`, then re-add the Mac `DYLD_LIBRARY_PATH` line.
3. Optional, to remove the new copy from history: in PyControl, `git revert 449ab4f` (plus any later H1 commits).
4. Update this handoff and `PAI_Lab/docs/MOVE_STATUS.md` to say which copy is canonical.

### Before you delete the backup

Do these in order; stop and ask the user if any step fails.

1. **Smoke test passes** (steps 1–4 above) from `PyControl/devices/H1_Lab`.
2. **Nothing needed lives only in the backup:**
   - `.env` → value already in `config.json` (`ftdi_device_id` `22040106`).
   - `.docx` guides, `H1_autosetup.md`, old handoff → superseded by `docs/*.md` and this file.
   - `h1_absorbance_test.py` → superseded by `h1_control.py absorbance`.
   - Old `h1_absorbance_*` result files → copy to `results/` (or elsewhere) if the user wants them.
3. **Find references:** `rg -n "H1_Lab_backup_20260929" ~/Documents/PyControl ~/Documents/PAI_Lab`. Update each hit to say the backup was deleted (date), and replace the **Undo** section above with "Undo no longer available locally; use git history."
4. **User confirms deletion** explicitly. Prefer moving to Trash over `rm`.
5. **Log it** in **Progress** and the migration table.

---

## Sibling projects

| Device folder | Handoff file | Status |
| --- | --- | --- |
| `Flex_Lab` | `FLEX_HANDOFF.md` | Active (PyControl) |
| `MiR_API` | `MIR_HANDOFF.md` | Active in PyControl (Desktop copy pending rename after smoke test) |
| `PAI_Lab` | (hub — separate) | `~/Documents/PAI_Lab` |

---

## Quick commands

```bash
cd /path/to/PyControl/devices/H1_Lab
source .venv/bin/activate   # Windows: .\.venv\Scripts\Activate.ps1
python h1_control.py status
```

---

## Guardrails

- Ask before tray motion or plate reads.
- No PyLabRobot inside `h1_gui.py`.
- Never commit `config.json` / `.env`.
- **Privacy (per `ALIGNMENT_HANDOFF.md`):** `docs/H1_SETUP.md` / `docs/H1_AUTOMATION.md` / code contain no real usernames (`~/...`, `%USERPROFILE%\...`, `<username>`). This handoff may hold real names, serials, and accurate paths, and ships in the team zip — but **never secrets**. Attribute entries `— <operator> on <HOSTNAME>`; label one-computer paths `(on <HOSTNAME>)`. Code derives paths from its own location.
- Don't fold hub code into this folder.

## User workflow preferences

- Beginner-friendly; plain English. "Type this into the Terminal:" with only the command in the code block.
- Small testable steps; ask before major operations.

---

## Open questions

- `pai_signal` vocabulary wiring (`ready_to_load`, `busy`, `reading`, `ready_to_unload`, `error`, `disconnected`) — when requested.
- Which Windows PC becomes the always-on station?

---

## Terms & Shorthand

| Term | Meaning |
| --- | --- |
| **H1** | Synergy H1, serial `22040106` |
| **H1_Lab** | This device folder |
| **PyControl** | Shared multi-device kit (`devices/*`) |
| **PAI_Lab** | Multi-device hub sibling (separate folder) |
| **Flex_Lab / MiR_API / Mantis** | Other peripheral device labs (same doc pattern) |
| **PAI** | The model/choreographer that will drive demos |
| **Always-on computer** | USB station PC for the H1 |
| **RDP** | Remote desktop into the always-on computer |
| **Station gateway** | Future hub LAN API (not needed for RDP demos) |
| **Demo contract / `pai_signal`** | Deferred coarse status cues for choreography |
| **`status`** | H1's read-only health check (Flex's `ping` equivalent) |
| **Device id / serial** | FTDI USB serial (Flex's IP equivalent) |
| **PLR** | PyLabRobot |
| **Handoff** | This file (`H1_HANDOFF.md`) |
