# MiR_API — Automation Brief

Upload this file into a chat so an agent can set up and verify the MiR CLI from a standard terminal with **minimal path confusion**.

## Goals

1. Ensure a **machine handoff** exists; create from `machines/MACHINE_HANDOFF.example.md` if missing (ask for git identity).
2. Locate or place the project under the **PyControl** layout (ask before creating folders).
3. Run the correct OS setup script (idempotent).
4. Configure robot host (**manual default** from `MIR_HANDOFF.md` / `.env`; do not invent IPs).
5. Verify with `Status` (read-only) → guided checks against **`MIR_HANDOFF.md`**.
6. Stop and report if a **manual gate** blocks progress.

## Canonical layout

```text
PyControl/
  ALIGNMENT_HANDOFF.md
  machines/<HOSTNAME>_HANDOFF.md
  devices/MiR_API/            ← this device
```

Preferred location: `~/PyControl` or `%USERPROFILE%\PyControl` (or machine handoff path).

**Path rule:** Never hard-code a real username in scripts or this brief. Use `~` / `%USERPROFILE%` / `<username>`.  
**Privacy scan:** Fix real homes in SETUP/AUTOMATION only; do not scrub accurate undo paths in `MIR_HANDOFF.md`.

**Config:** MiR uses `.env` / `.env.example` (gitignored `.env`). Never print `MIR_PASSWORD` or auth headers.

## Zip / USB (no git clone)

1. Ask the user where the unzipped `PyControl` folder is.
2. If missing, **ask permission** before creating `~/PyControl` (or `%USERPROFILE%\PyControl`) and copying/extracting into it.
3. If the user says no, stop and tell them exactly which folder to provide.

## OS detection → setup command

| OS | Command |
| --- | --- |
| macOS | `chmod +x "$DEVICE_DIR/scripts/setup_mac.sh" && "$DEVICE_DIR/scripts/setup_mac.sh" --non-interactive --ip <ROBOT_IP>` |
| Linux | `chmod +x "$DEVICE_DIR/scripts/setup_linux.sh" && "$DEVICE_DIR/scripts/setup_linux.sh" --non-interactive --ip <ROBOT_IP>` |
| Windows | `powershell -ExecutionPolicy Bypass -File "$DEVICE_DIR\scripts\setup_windows.ps1" -NonInteractive -Ip <ROBOT_IP>` |

Take `<ROBOT_IP>` from `MIR_HANDOFF.md` or existing `.env`.  
Interactive host prompt (human present): run the script **without** `--non-interactive`.

Scripts print `SETUP OK` (exit 0) or `SETUP INCOMPLETE` (exit 1).

## Manual gates (do not invent workarounds)

| Gate | Agent action |
| --- | --- |
| Robot off / wrong Wi‑Fi | Ask user to power on and join the facility SSID from `MIR_HANDOFF.md` |
| Python missing | Give OS-specific hint from MIR_SETUP.md; do not install system packages without permission |
| `.env` missing credentials | Ensure `.env` exists from example; **ask the user** to fill username/password locally — never invent secrets |
| Browser cannot open robot UI | Stop; networking is a human/IT problem |
| User denies creating `~/PyControl` | Stop; ask for existing path |

## Verification checklist (guide the user)

Run from `DEVICE_DIR` with `.venv` active (setup script already does this):

1. `python mir_command.py Status` → connected; name/IP match **`MIR_HANDOFF.md`** (read-only)
2. Optional: `python mir_command.py ListPositions` / `ListMissions` (read-only)
3. **Ask before** `GoToPosition` / `RunMission` / GUI **Start** (motion)
4. Optional: `python -m gui` or `./run_gui.sh` (user clicks; ask before Start)

## Idempotency

Re-running setup scripts is safe: reuse `.venv`, refresh requirements, keep `.env`, optionally rewrite `MIR_HOST` via `--ip`, run `Status` again.

## After success

Point the human to `docs/MIR_USER_GUIDE.md`.  
Device brief: **`MIR_HANDOFF.md`**.  
Deep API notes: `docs/PROJECT_KNOWLEDGE.md`.  
If aligning other devices, use the repo-root **`ALIGNMENT_HANDOFF.md`**.
