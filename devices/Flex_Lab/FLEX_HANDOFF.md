# FLEX_HANDOFF — Opentrons Flex

Living device brief for **Opentrons Flex** under the shared **PyControl** layout.  
**Update this file whenever objectives, progress, or durable facts change.**

Filename convention: device handoffs are `<TAG>_HANDOFF.md` (this file = `FLEX_HANDOFF.md`). See repo-root `ALIGNMENT_HANDOFF.md`.

---

## How to update this document

1. Read at session start.
2. Edit before ending work that changes goals, status, config, or next steps.
3. Keep concise; prefer bullets.
4. Do not delete durable facts unless proven wrong — replace with a dated correction.
5. Set **Last updated** to today when you change Progress or Durable details.
6. Secrets stay in local config / env — not here. This file ships in the team zip (real names, IPs, serials OK).
   - Attribute entries `— <operator> on <HOSTNAME>` (or `(via agent)`); label one-computer paths `(on <HOSTNAME>)`. See `ALIGNMENT_HANDOFF.md` privacy rules.
7. If docs/scripts/CLI behavior change, also update `FLEX_README.md`, `docs/FLEX_SETUP.md`, `docs/FLEX_USER_GUIDE.md`, `docs/FLEX_AUTOMATION.md`, and repo-root `ALIGNMENT_HANDOFF.md` if the shared pattern changed.

---

## Last updated

2026-09-30 — Renamed everyday docs to tagged names (`FLEX_README.md`, `docs/FLEX_SETUP.md`, `docs/FLEX_USER_GUIDE.md`, `docs/FLEX_AUTOMATION.md`); no bare README stub. Alignment doc updated with the same convention. — Jesse Martin (via agent) on WS-RHCV7HYY6K

Earlier 2026-09-30 — Added Smoke test / Undo / Before-you-delete-backup sections and attribution rule (from H1 chat, per updated `ALIGNMENT_HANDOFF.md`). — Jesse Martin (via agent) on WS-RHCV7HYY6K

Earlier 2026-09-30 — Privacy rules: SETUP/AUTOMATION/Alignment generalized; device handoff keeps durable facts; machine handoff convention added.

---

## Objectives

### In scope

Lean Python CLI so humans or a PAI can choreograph Flex demo operations over Wi‑Fi (deck awareness, run/upload protocols, transfer helper, status, file signals). Cross-platform. Easy setup. No overbuilding.

### Out of scope (guide only)

Full PAI orchestration, research LIMS, installer/Docker/systemd packaging.

---

## Progress

| Status | Item |
| --- | --- |
| Done | Control layer `flex_control.py` + demo protocol |
| Done | Live smoke test (historical): ping/status/deck/protocols/signals vs Chemelian |
| Done | PyControl layout: `devices/Flex_Lab/` |
| Done | `docs/FLEX_SETUP.md`, `docs/FLEX_USER_GUIDE.md`, `docs/FLEX_AUTOMATION.md`, `FLEX_README.md` (tagged names) |
| Done | `scripts/setup_mac.sh`, `setup_linux.sh`, `setup_windows.ps1` |
| Done | `config.example.json` + discover/`--set-ip` |
| Done | Re-verify `ping` after restructure (`ping_ok` / Chemelian) |
| Done | Initial git commit `8966991` (PyControl root) |
| Done | Guided live `run` (Demo) and `transfer` motion tests |
| Done | Terminal prompts for pause-resume and Ctrl+C → optional Flex stop |
| Done | Demo + terminal pause-resume prompt verified live |
| Done | H1_Lab migrated into `devices/H1_Lab` (`SETUP OK` 2026-09-29) |
| Done | Device handoff renamed to `FLEX_HANDOFF.md` |
| Pending | MiR_API migrated into `devices/` via Alignment Handoff |
| Pending | Commit recent Flex CLI/docs/handoff renames |
| Pending | User creates zip after all three devices work |

### Next steps

1. Fill **git identity** (and confirm hostname) in `../../machines/WS-RHCV7HYY6K_HANDOFF.md` (or rename file if Computer Name differs).
2. Align **MiR_API** via `ALIGNMENT_HANDOFF.md` → `devices/MiR_API` + `MIR_HANDOFF.md`.
3. Commit shareable doc changes (machine `*_HANDOFF.md` stays gitignored).
4. After MiR verifies: commit, then build the zip with `git archive` (see `ALIGNMENT_HANDOFF.md` → **Sharing / zip**); never Finder “Compress”.

---

## Durable details

### Network / robot

| Field | Value |
| --- | --- |
| Wi‑Fi | `optrn-nyc1-robotics` (WPA‑PSK) |
| Flex IP | `10.14.19.180` |
| API | `http://10.14.19.180:31950` |
| Name | Chemelian |
| Model | OT-3 Standard (Flex) |
| Serial | `FLXA2020241115005` |

### Hardware

- Right: Flex 50 µL (`flex_1channel_50` / `p50_single_flex`), 5–50 µL
- Trash fixture: **A3**
- Common demo labware: tiprack 50 µL @ **B2**; PCR plate @ **C2**

### Paths (this device)

| Path | Role |
| --- | --- |
| `flex_control.py` | CLI + library |
| `config.example.json` | Committed defaults |
| `config.json` | Local IP (may be gitignored at pack level) |
| `docs/` | Setup, User, Automation |
| `scripts/` | OS setup entrypoints |
| `protocols/demo_transfer.py` | Parameterized demo |
| `signals/` | Choreography handshakes |
| `FLEX_HANDOFF.md` | This file |

### Sibling projects

| Device folder | Handoff file | Status |
| --- | --- | --- |
| `MiR_API` | `MIR_HANDOFF.md` (when migrated) | Pending — often `~/Desktop/MiR_API` |
| `H1_Lab` | `H1_HANDOFF.md` | Migrated → `PyControl/devices/H1_Lab` |

Follow repo-root **ALIGNMENT_HANDOFF.md** — do not invent a second PyControl tree if one already exists.

---

## Quick commands

```bash
cd /path/to/PyControl/devices/Flex_Lab
source .venv/bin/activate   # Windows: .\.venv\Scripts\Activate.ps1
python flex_control.py ping
```

---

## Smoke test (run after any change to code, paths, or setup)

Run from the device folder with `.venv` active, on robot Wi‑Fi. Steps 1–2 are agent-safe; steps 3–4 need the robot; step 5 moves hardware (**ask first**).

| Step | Command | Pass looks like | Moves? |
| --- | --- | --- | --- |
| 1. Code loads | `python -m py_compile flex_control.py && python flex_control.py --help` | No errors; usage text | No |
| 2. Scripts parse (Mac/Linux) | `bash -n scripts/setup_mac.sh && bash -n scripts/setup_linux.sh` | No output | No |
| 3. Robot reachable | `python flex_control.py ping` | `"event": "ping_ok"`, name `Chemelian` | No |
| 4. Robot state | `python flex_control.py status` then `python flex_control.py protocols` | Right-mount P50; protocol list | No |
| 5. Motion | `python flex_control.py run "Demo"` (or a `transfer`) | Run completes | **Yes** |

Log the result (date + pass/fail + `— <operator> on <HOSTNAME>`) in **Progress**.

## Undo

No pre-migration backup folder was kept: the old `~/Documents/Flex_Lab` was moved (not copied) into `PyControl/devices/Flex_Lab` in commit `8966991`. Undo = git history:

1. In PyControl, `git log -- devices/Flex_Lab` to find the commit to return to.
2. `git checkout <commit> -- devices/Flex_Lab` (or `git revert <commit>`), then re-run the setup script.
3. Update this handoff to say what was reverted.

## Before you delete the backup

Not applicable — no `Flex_Lab_backup_<YYYYMMDD>` exists. If one is created in the future, follow the checklist in `ALIGNMENT_HANDOFF.md` → **Before you delete the backup**.

---

## Open questions

- Demo choreography stage names with PAI / manipulator?
