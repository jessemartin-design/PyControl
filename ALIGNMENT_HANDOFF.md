# Alignment Handoff — PyControl device CLIs

**Purpose:** Upload this document into a Cursor (or similar) chat for **MiR_API**, **H1_Lab**, or any future device project. Instruct the agent: *“Follow ALIGNMENT_HANDOFF.md to bring this project into the PyControl layout and verify it works.”*

This file standardizes structure, docs, setup automation, naming, and guided confirmation across devices.

---

## How agents must use this file

1. Read this entire document before changing files.
2. Ask the user only when a **decision gate** below requires it; otherwise automate.
3. Prefer editing/moving into an **existing** `PyControl/` tree rather than inventing a second one.
4. After changes: update the device `HANDOFF.md`, run the verification checklist with the user, and summarize what moved where.
5. Do **not** create share zips unless the user asks (zips go stale if made too early).
6. Do **not** add installer apps, Docker, or systemd services unless the user explicitly requests them.

---

## Target layout (canonical)

```text
PyControl/
  README.md
  ALIGNMENT_HANDOFF.md
  templates/
    SETUP.md
    USER_GUIDE.md
    AUTOMATION.md
    HANDOFF.md
    README.md
  devices/
    Flex_Lab/     # Opentrons Flex
    MiR_API/      # MiR robot
    H1_Lab/       # Biotek H1
    <NewDevice>/  # future
```

### Preferred machine paths

| OS | PyControl root |
| --- | --- |
| Mac / Linux | `~/PyControl` |
| Windows | `%USERPROFILE%\PyControl` |

**Development note (this lab Mac):** a working tree may live at `~/Documents/PyControl` after renaming the old `Flex_Lab` repo. That is fine. New USB installs should still target `~/PyControl` unless the user chooses otherwise.

### Path rule

- Resolve the device root as the folder that contains the device’s main CLI module + `config.example.json` (or equivalent).
- Never hard-code another user’s home path in scripts.
- Setup scripts must compute `DEVICE_DIR` from the script location so zip/USB paths work.

---

## Known projects to align

| Device folder name | Role | Known prior location (lab Mac) |
| --- | --- | --- |
| `Flex_Lab` | Opentrons Flex | Was `Documents/Flex_Lab` → should already be `PyControl/devices/Flex_Lab` |
| `MiR_API` | MiR API control | `Desktop/MiR_API` |
| `H1_Lab` | Biotek H1 control | `Documents/H1_Lab` |

When aligning MiR or H1: **migrate into the existing PyControl** that already contains Flex_Lab, if present.

---

## Decision gates (ask the user)

| Gate | Question | Default if user defers |
| --- | --- | --- |
| PyControl missing | “Create `~/PyControl` (or Windows equivalent) and place this device under `devices/<Name>/`?” | Wait for yes/no — **do not create without permission** |
| Two PyControl copies | “Which tree is canonical? Merge into that one.” | Prefer the one that already has `devices/Flex_Lab` |
| Device IP / host | Manual entry vs auto-discover (if supported) | **Manual** with value from existing config |
| Destructive moves | Confirm before deleting the old project folder | Leave old folder until user confirms delete |
| Motion / wet tests | Confirm before commands that move robots or run assays | Ping/status only until approved |

---

## Naming & rename checklist

When bringing a project into PyControl, the **device directory name** must match the table above (`MiR_API`, `H1_Lab`, `Flex_Lab`, or an agreed new name).

### Required renames / reference updates

Update every user-facing and agent-facing reference that still points at the old standalone root:

| Area | What to change |
| --- | --- |
| Folder | Final path `PyControl/devices/<DeviceName>/` |
| README titles | Say `PyControl / devices / <DeviceName>` |
| Docs examples | `cd` examples use `$HOME/PyControl/devices/<DeviceName>` or `%USERPROFILE%\PyControl\devices\<DeviceName>` |
| Setup scripts | Live under `devices/<DeviceName>/scripts/`; derive paths from script location |
| Config | Commit `config.example.json`; keep local `config.json` machine-specific |
| Automation brief | Path rule = directory containing the main CLI entry file |
| Handoff | List sibling devices; link to repo-root `ALIGNMENT_HANDOFF.md` |
| Imports / packaging | If code assumed repo root == device root, fix relative paths |
| Old name strings | Search for old folder names (`Flex_Lab` repo root assumptions, `MiR_API` desktop paths, etc.) and replace in docs/scripts |

### Creating a new device name

1. Agree on `Pascal_or_Snake` folder name with the user (e.g. `MiR_API`).
2. Copy `templates/` into `devices/<NewName>/docs/` (and device README/HANDOFF).
3. Replace placeholders `__DEVICE_NAME__`, `__CLI_MODULE__`, `__PING_COMMAND__`, `__WIFI_OR_NETWORK__`, `__DEFAULT_HOST__`.

---

## Required deliverables per device

Mirror **Flex_Lab** unless a difference is justified in that device’s HANDOFF:

| Item | Intent |
| --- | --- |
| Main CLI module | e.g. `flex_control.py`, `mir_command.py`, `h1_control.py` |
| `requirements.txt` | Minimal deps |
| `config.example.json` | Safe committed defaults |
| `config.json` | Local (optional gitignore) |
| `docs/SETUP.md` | Mac + Windows + Linux; troubleshooting **tables** |
| `docs/USER_GUIDE.md` | Activate venv + command cheat sheet |
| `docs/AUTOMATION.md` | Agent brief: paths, permission to create folders, verify |
| `HANDOFF.md` | Objectives, progress, durable facts, update rules |
| `README.md` | Short index linking the docs |
| `scripts/setup_mac.sh` | Idempotent |
| `scripts/setup_linux.sh` | Idempotent |
| `scripts/setup_windows.ps1` | Idempotent |
| Signals or equivalent | Only if choreography needs them |

### Setup script behavior (all OS)

1. Resolve `DEVICE_DIR` from script path.
2. Require Python **3.9+** (prefer 3.9–3.12 when choosing a binary).
3. Create `.venv` if missing; reuse if present.
4. `pip install -r requirements.txt`.
5. Ensure config from example.
6. Prompt (or flags) for **manual host/IP** vs **discover** when the device supports discovery; default manual.
7. Run the device ping/health command; print clear `SETUP OK` / failure.

Support non-interactive flags analogous to Flex:

- `--non-interactive --ip <addr>` / `-NonInteractive -Ip <addr>`
- optional `--discover` / `-Discover`

### Docs behavior

- Setup & User troubleshooting sections use **markdown tables**.
- Do not require launching vendor GUIs for CLI setup (optional appendix only).
- Success gate is one obvious health command (Flex: `ping` → `ping_ok`).

---

## Migration procedure (MiR_API / H1_Lab / future)

### A. Find PyControl

1. Search common locations: `~/PyControl`, `~/Documents/PyControl`, workspace parent folders.
2. If found and contains `devices/Flex_Lab`, treat it as canonical.
3. If not found → **ask permission** to create `~/PyControl` and copy `ALIGNMENT_HANDOFF.md`, `README.md`, and `templates/` from the Flex-based kit (or recreate from this spec).

### B. Create device slot

```text
PyControl/devices/MiR_API/   # or H1_Lab
```

### C. Move code

1. Copy/move source, requirements, existing docs into the device slot.
2. Do not copy `.venv` (recreate with setup script).
3. Keep git history when possible (user decision): either move the whole repo to become PyControl, or add device files into the existing PyControl git root and retire the old repo later.

### D. Align structure

1. Add missing docs/scripts using `templates/` + Flex_Lab as the reference implementation.
2. Apply rename checklist.
3. Implement host/IP prompt pattern appropriate to that API.
4. Update device `HANDOFF.md` with durable network/device facts from the old project.

### E. Guided verification (do this with the user)

1. Network/Wi‑Fi connected as required by that device.
2. Run setup script for the OS.
3. Health/ping command succeeds.
4. One read-only status command succeeds.
5. **Ask** before any motion, navigation, aspirate, or plate read that changes the physical world.
6. Mark Progress in `HANDOFF.md`.

### F. After all three devices pass

User will zip `PyControl` (excluding `.venv` folders) for USB share. Agents may list exclude patterns but should not zip unless asked.

---

## Flex_Lab reference commands

```bash
cd "$HOME/PyControl/devices/Flex_Lab"   # or Documents/PyControl/...
source .venv/bin/activate
python flex_control.py ping
python flex_control.py status
```

Setup:

```bash
./scripts/setup_mac.sh
./scripts/setup_linux.sh
# Windows: .\scripts\setup_windows.ps1
```

---

## Template placeholders

When copying from `templates/`, replace:

| Placeholder | Example |
| --- | --- |
| `__DEVICE_NAME__` | `MiR_API` |
| `__CLI_MODULE__` | `mir_command.py` |
| `__PING_COMMAND__` | `python mir_command.py status` |
| `__WIFI_OR_NETWORK__` | device network name |
| `__DEFAULT_HOST__` | IP or hostname |
| `__SETUP_SCRIPT_MAC__` | `scripts/setup_mac.sh` |

---

## What “done” means for an alignment pass

- [ ] Device lives at `PyControl/devices/<DeviceName>/`
- [ ] Setup scripts exist and are idempotent
- [ ] SETUP / USER_GUIDE / AUTOMATION / HANDOFF present and path-correct
- [ ] Config example committed; local config works
- [ ] User completed guided verification (ping/status at minimum)
- [ ] Device HANDOFF Progress updated
- [ ] No second competing PyControl tree left unexplained

---

## Maintenance

Any agent that changes the shared pattern (layout, script flags, doc set) must update **this** `ALIGNMENT_HANDOFF.md` and the Flex reference implementation so MiR/H1 stays consistent.
