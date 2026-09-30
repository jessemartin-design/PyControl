# Alignment Handoff — PyControl device CLIs

**Purpose:** Upload this document into a Cursor (or similar) chat for **MiR_API**, **H1_Lab**, or any future device project. Instruct the agent: *“Follow ALIGNMENT_HANDOFF.md to bring this project into the PyControl layout and verify it works.”*

This file standardizes structure, docs, setup automation, naming, and guided confirmation across devices.

---

## How agents must use this file

1. Read this entire document before changing files.
2. Ask the user only when a **decision gate** below requires it; otherwise automate.
3. Prefer editing/moving into an **existing** `PyControl/` tree rather than inventing a second one.
4. After changes: update that device’s **`<TAG>_HANDOFF.md`**, run the verification checklist with the user, and summarize what moved where.
5. Do **not** create share zips unless the user asks (zips go stale if made too early).
6. Do **not** add installer apps, Docker, or systemd services unless the user explicitly requests them.
7. On every alignment or setup pass: ensure a **machine handoff** exists (see below); create/update it if missing.
8. Scan **SETUP / USER-facing setup sections / AUTOMATION / this Alignment doc** for real OS usernames or hard-coded home paths. Fix those docs automatically. **Do not** scrub accurate historical paths or durable device facts out of `<TAG>_HANDOFF.md` files.

---

## Privacy & path conventions (read carefully)

| Document type | Real OS username (`jesse…` style)? | Site robot name / serial / IP? |
| --- | --- | --- |
| `docs/SETUP.md`, `docs/AUTOMATION.md`, `ALIGNMENT_HANDOFF.md`, `templates/*` | **No** — use `~/…`, `%USERPROFILE%\…`, or `/Users/<username>/…` | **Generalize** — use placeholders; point to device or machine handoff for live values |
| `<TAG>_HANDOFF.md` (e.g. `FLEX_HANDOFF.md`) | **Allowed when accuracy requires it** (undo/backup paths). Prefer `~/…` when equivalent | **Keep** — Chemelian, serials, IPs, Wi‑Fi SSIDs belong here |
| `machines/<HOST>_HANDOFF.md` | **Yes — this is the place** for operator name, git identity, host IP | Optional pointers to which devices this PC drives |

**Accuracy over scrubbing:** If a redirect/undo instruction only works with the real absolute path, keep that path in the **device handoff**. Do not invent scrubbed paths that break recovery steps.

**Alignment check (automatic):** When aligning any project, search its SETUP/AUTOMATION (and Alignment copies) for `/Users/<realname>` or `C:\Users\<realname>`. Replace with `~/` / `%USERPROFILE%` / `<username>` placeholders. If nothing to fix, move on. Leave `<TAG>_HANDOFF.md` historical sections intact unless the user asks to edit them.

---

## Machine handoff (per computer — required)

Shared facts that apply to **all devices on one PC** live in:

```text
PyControl/machines/<HOSTNAME>_HANDOFF.md
```

Example template (committed): `machines/MACHINE_HANDOFF.example.md`  
Real machine files are **gitignored** so USB/zip shares do not leak identity.

### Strategy (why this is a good idea)

- Agents cannot rely on chat memory across projects; a file on disk is the durable “memory.”
- Separates **person/computer** facts from **device** facts (Flex vs H1 vs MiR).
- Gitignored machine files keep personal email/IP out of shared zips; the example file teaches the shape.

### What to store

| Field | Notes |
| --- | --- |
| Operator display name | Human using this PC |
| Git `user.name` / `user.email` | From user prompt; also applied via `git config` when user agrees |
| Computer name / hostname | For the filename and docs |
| Last-known LAN IP | Volatile — refresh when networking changes |
| Preferred `PyControl` path | e.g. `~/Documents/PyControl` or `~/PyControl` |
| OS | macOS / Windows / Linux |
| Notes | Lab Wi‑Fi names, etc., if useful across devices |

### Agent procedure (setup / automation / alignment)

1. Detect hostname (`scutil --get ComputerName` / `hostname` / Windows `hostname`).
2. If `machines/<HOSTNAME>_HANDOFF.md` is missing, **ask the user** for the fields above (especially git name + email).
3. Create the file from the example template; do not commit it.
4. With user permission, set git identity for commits on this machine:
   - `git config --global user.name "…"`
   - `git config --global user.email "…"`
5. On later setups, **read** the machine handoff first; only ask again if fields are blank or the user wants updates.
6. If the preferred PyControl folder is missing, **ask** to create `~/PyControl` or choose another path — do not invent a username-specific absolute path in SETUP/AUTOMATION text.

---

## Target layout (canonical)

```text
PyControl/
  README.md
  ALIGNMENT_HANDOFF.md
  machines/
    MACHINE_HANDOFF.example.md
    <HOSTNAME>_HANDOFF.md      ← local only (gitignored)
  templates/
    SETUP.md
    USER_GUIDE.md
    AUTOMATION.md
    DEVICE_HANDOFF.md
    README.md
  devices/
    Flex_Lab/FLEX_HANDOFF.md
    MiR_API/MIR_HANDOFF.md
    H1_Lab/H1_HANDOFF.md
```

### Preferred machine paths (generic docs)

| OS | PyControl root |
| --- | --- |
| Mac / Linux | `~/PyControl` (or path recorded in the machine handoff) |
| Windows | `%USERPROFILE%\PyControl` |

### Path rule (code + generic docs)

- Resolve device root from the folder that contains the CLI + `config.example.json`.
- Never hard-code a real home path in **scripts** or **SETUP/AUTOMATION**.
- Setup scripts compute `DEVICE_DIR` from their own location (zip/USB safe).

---

## Device handoff naming convention (required)

| Device folder | Handoff filename | Tag |
| --- | --- | --- |
| `Flex_Lab` | `FLEX_HANDOFF.md` | `FLEX` |
| `MiR_API` | `MIR_HANDOFF.md` | `MIR` |
| `H1_Lab` | `H1_HANDOFF.md` | `H1` |
| Future device | `<TAG>_HANDOFF.md` | Agree short uppercase tag with user |

1. Repo-root alignment kit stays **`ALIGNMENT_HANDOFF.md`**.
2. Each device owns **exactly one** `<TAG>_HANDOFF.md` at the device root.
3. Rename legacy `HANDOFF.md` → `<TAG>_HANDOFF.md` and fix links.
4. Title like `# FLEX_HANDOFF — Opentrons Flex`.
5. Sibling tables list other devices’ **folder + handoff filename**.

---

## Known projects to align

| Device folder | Role | Typical prior location (examples) | Handoff |
| --- | --- | --- | --- |
| `Flex_Lab` | Opentrons Flex | `PyControl/devices/Flex_Lab` | `FLEX_HANDOFF.md` |
| `MiR_API` | MiR API control | `~/Desktop/MiR_API` | `MIR_HANDOFF.md` |
| `H1_Lab` | Biotek H1 | See `H1_HANDOFF.md` for backup/undo paths | `H1_HANDOFF.md` |

Prefer one PyControl tree; add device folders into it.

---

## Decision gates (ask the user)

| Gate | Question | Default if user defers |
| --- | --- | --- |
| PyControl missing | Create preferred path from machine handoff / `~/PyControl`? | Wait for yes/no |
| Two PyControl copies | Which tree is canonical? | Prefer one with `devices/Flex_Lab` |
| Machine handoff missing | Collect operator + git identity + host fields? | Required before finishing setup |
| Device IP / host | Manual vs discover | **Manual** default |
| Destructive moves | Confirm before deleting backups | Leave until explicit yes |
| Motion / wet tests | Confirm before physical actions | Health checks only until approved |

---

## Naming & rename checklist

| Area | What to change |
| --- | --- |
| Folder | `PyControl/devices/<DeviceName>/` |
| Docs examples | `~/PyControl/devices/<DeviceName>` or `%USERPROFILE%\…` |
| Setup scripts | Under `scripts/`; path from script location |
| Config | `config.example.json` committed; `config.json` local |
| Device handoff | `<TAG>_HANDOFF.md` with **real** device durable facts |
| SETUP/AUTOMATION | Placeholders only for usernames and live robot IDs |
| Machine handoff | Ensure `machines/<HOST>_HANDOFF.md` exists |

### Creating a new device

1. Agree folder name + **TAG**.
2. Copy templates; write `<TAG>_HANDOFF.md` from `DEVICE_HANDOFF.md`.
3. Replace placeholders (`__DEVICE_NAME__`, `__DEVICE_TAG__`, etc.).

---

## Required deliverables per device

| Item | Intent |
| --- | --- |
| Main CLI + `requirements.txt` | Lean control layer |
| `config.example.json` / local `config.json` | Defaults vs machine |
| `docs/SETUP.md` | OS install; **tables**; no real usernames; robot IDs as placeholders + “see device handoff” |
| `docs/USER_GUIDE.md` | Everyday commands (may reference this lab’s devices) |
| `docs/AUTOMATION.md` | Agent brief; machine handoff + folder permission gates |
| `<TAG>_HANDOFF.md` | Durable device facts (names, serials, IPs, undo paths) |
| `scripts/setup_*.sh` / `.ps1` | Idempotent |

### Setup script behavior

1. Resolve `DEVICE_DIR` from script path.
2. Python 3.9+.
3. Reuse or create `.venv`; `pip install -r requirements.txt`.
4. Ensure config from example.
5. Manual host/IP by default; optional discover.
6. Ping/health → `SETUP OK` / failure.
7. (Agent-driven setups) ensure machine handoff + git identity per sections above.

Flags: `--non-interactive --ip …`, optional `--discover`.

---

## Migration procedure

### A–F (summary)

Find/create PyControl (ask permission) → create `devices/<Name>/` → move code (no `.venv`) → align docs/scripts/`<TAG>_HANDOFF.md` → scrub SETUP/AUTOMATION usernames if needed → ensure machine handoff → guided verify → mark Progress in device handoff.

Retired copies: rename to `<Folder>_backup_<YYYYMMDD>` (never delete during migration). Record accurate undo paths in **device** handoff.

---

## Flex reference (generic automation wording)

```bash
cd "$HOME/PyControl/devices/Flex_Lab"   # or path from machines/<HOST>_HANDOFF.md
source .venv/bin/activate
python flex_control.py ping
python flex_control.py status
```

Expect `ping_ok`. Confirm robot **name / IP** against `devices/Flex_Lab/FLEX_HANDOFF.md` (not hard-coded in this Alignment file).

---

## Template placeholders

| Placeholder | Example |
| --- | --- |
| `__DEVICE_NAME__` | `MiR_API` |
| `__DEVICE_TAG__` | `MIR` |
| `__CLI_MODULE__` | `mir_command.py` |
| `__PING_COMMAND__` | `python mir_command.py status` |
| `__WIFI_OR_NETWORK__` | (see device handoff) |
| `__DEFAULT_HOST__` | (see device handoff / config.example) |
| `__DEVICE_HANDOFF_FILE__` | `MIR_HANDOFF.md` |

---

## What “done” means for an alignment pass

- [ ] Device at `PyControl/devices/<DeviceName>/`
- [ ] Setup scripts idempotent
- [ ] SETUP / USER_GUIDE / AUTOMATION path-correct; SETUP/AUTOMATION free of real usernames
- [ ] `<TAG>_HANDOFF.md` present with durable device facts
- [ ] `machines/<HOSTNAME>_HANDOFF.md` present (gitignored) with git identity
- [ ] Guided verification done
- [ ] Progress updated in device handoff

---

## Maintenance

Update **this** file when the shared pattern changes (including machine-handoff or privacy rules). Keep Flex `docs/SETUP.md` / `docs/AUTOMATION.md` as the reference implementation for generic wording.
