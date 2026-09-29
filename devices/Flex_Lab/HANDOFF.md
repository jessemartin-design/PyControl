# Flex_Lab — Agent Handoff

Living device brief for **Opentrons Flex** under the shared **PyControl** layout.  
**Update this file whenever objectives, progress, or durable facts change.**

---

## How to update this document

1. Read at session start.
2. Edit before ending work that changes goals, status, config, or next steps.
3. Keep concise; prefer bullets.
4. Do not delete durable facts unless proven wrong — replace with a dated correction.
5. Set **Last updated** to today when you change Progress or Durable details.
6. Secrets stay in local config / env — not here.
7. If docs/scripts/CLI behavior change, also update `docs/SETUP.md`, `docs/USER_GUIDE.md`, `docs/AUTOMATION.md`, and repo-root `ALIGNMENT_HANDOFF.md` if the shared pattern changed.

---

## Last updated

2026-09-29 — Restructured into PyControl; added Setup/User/Automation docs, OS setup scripts, IP manual/discover flow.

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
| Done | `docs/SETUP.md`, `USER_GUIDE.md`, `AUTOMATION.md` |
| Done | `scripts/setup_mac.sh`, `setup_linux.sh`, `setup_windows.ps1` |
| Done | `config.example.json` + discover/`--set-ip` |
| Pending | Re-verify `ping` after restructure on this machine |
| Pending | First guided live `run` / `transfer` (ask user) |
| Pending | MiR_API + H1_Lab migrated into `devices/` via Alignment Handoff |
| Pending | User creates zip after all three devices work |

### Next steps

1. Run device setup script / `ping` to confirm post-move.
2. Upload `ALIGNMENT_HANDOFF.md` into MiR_API and H1_Lab chats to migrate those projects.
3. Guided confirm checklist per device; then zip `PyControl` for USB share.

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
| `HANDOFF.md` | This file |

### Sibling projects (migrate later)

| Device folder | Current location (this Mac, pre-migration) |
| --- | --- |
| `MiR_API` | `/Users/jesse.martin/Desktop/MiR_API` |
| `H1_Lab` | `/Users/jesse.martin/Documents/H1_Lab` |

Follow repo-root **ALIGNMENT_HANDOFF.md** — do not invent a second PyControl tree if one already exists.

---

## Quick commands

```bash
cd /path/to/PyControl/devices/Flex_Lab
source .venv/bin/activate   # Windows: .\.venv\Scripts\Activate.ps1
python flex_control.py ping
```

---

## Open questions

- Demo choreography stage names with PAI / manipulator?
- Confirm wet deck before first `transfer`.
