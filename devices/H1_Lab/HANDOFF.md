# H1_Lab — Agent Handoff

Living device brief for the **BioTek Synergy H1** under the shared **PyControl** layout.  
**Update this file whenever objectives, progress, or durable facts change.**

---

## How to update this document

1. Read at session start.
2. Edit before ending work that changes goals, status, config, or next steps.
3. Keep concise; prefer bullets.
4. Do not delete durable facts unless proven wrong — replace with a dated correction.
5. Set **Last updated** to today when you change Progress or Durable details.
6. Secrets stay in local config / env — not here.
7. If docs/scripts/CLI behavior change, also update `docs/SETUP.md`, `docs/USER_GUIDE.md`, `docs/AUTOMATION.md`, and repo-root [`ALIGNMENT_HANDOFF.md`](../../ALIGNMENT_HANDOFF.md) if the shared pattern changed.

---

## Last updated

2026-09-29 — Migrated into `PyControl/devices/H1_Lab`; setup scripts, docs, `config.json`, `results/`, `discover` added. User ran `setup_mac.sh` → `SETUP OK`; old-path pointers updated.

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
| Done | `docs/SETUP.md`, `USER_GUIDE.md`, `AUTOMATION.md` |
| Done | User ran `setup_mac.sh` → `SETUP OK` (`status` from new path) |
| Done | Repointed `PAI_Lab` stubs/docs, `MiR_API/docs/PROJECT_KNOWLEDGE.md`, PyControl README, Flex HANDOFF |
| Done | Git ignore verified: `config.json` and `.venv` excluded (`git check-ignore`) |
| Done | Tray `open` → `close` from new path (user-verified 2026-09-29) |
| Pending | Git commit after tray test (user approved; nothing committed yet) |
| Decided | Old `~/Documents/H1_Lab` kept as backup |
| Pending | Windows / Linux hardware verification |
| Deferred | `pai_signal` emit from CLI/GUI ("demo contract") |

### Next steps

User decisions (2026-09-29):

1. **Tray test** — yes: guided `open` → `close` from the new path (no GUI). **Passed.**
2. **Git commit** — yes, **after** the tray test passes (PyControl root; `config.json` / `.venv` excluded).
3. **Old `~/Documents/H1_Lab`** — **keep as backup** for now (only copy of `.docx` guides, `h1_absorbance_test.py`, old results). Do not delete without explicit confirmation.

Session notes:

- `PAI_Lab/h1_absorbance_test.py` stub intentionally still points to old `~/Documents/H1_Lab` (script not migrated).
- Edited `PAI_Lab/h1_control.py` / `h1_gui.py` stubs were not executed (auto-review blocks running scripts outside the active workspace); they only print a redirect and exit 2.
- Current Cursor workspace is still the old `~/Documents/H1_Lab`, so commands touching `PyControl`/`PAI_Lab` may trigger approval prompts.

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
| `HANDOFF.md` | This file |

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
| 2026-09-29 | Copied into `PyControl/devices/H1_Lab`; `.env` → `config.json`; outputs → `results/`; `requests` dropped from requirements; old docs replaced by `docs/SETUP.md` / `USER_GUIDE.md` / `AUTOMATION.md` |

Not copied (still in old folder): `.docx` guides, `h1_absorbance_test.py`, old result files, `H1_autosetup.md`, old handoff.

**If something breaks after the move:**

1. `cwd` is `PyControl/devices/H1_Lab`, not `~/Documents/H1_Lab` or `PAI_Lab`.
2. Use this folder's `.venv` (re-run the setup script to rebuild it).
3. Missing serial? `config.json` exists but lacks `ftdi_device_id` → `.env` is ignored once `config.json` exists.
4. `PAI_Lab/h1_*.py` are redirect stubs only.

**Revert:** the old project at `/Users/jesse.martin/Documents/H1_Lab` is untouched and still works (`.venv/bin/python3 h1_control.py status` there). To undo the migration, keep using it and delete `PyControl/devices/H1_Lab` contents except the placeholder README. To rebuild this venv: delete `.venv`, re-run `scripts/setup_mac.sh`.

---

## Sibling projects

| Device folder | Status |
| --- | --- |
| `Flex_Lab` | Active (PyControl) |
| `MiR_API` | See its own HANDOFF — do not modify for H1 work |
| `PAI_Lab` | Hub, separate folder `~/Documents/PAI_Lab` |

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
| **Handoff** | This file |
