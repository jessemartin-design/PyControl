# H1_Lab — Automation Brief

Upload this file into a chat so an agent can set up and verify the H1 CLI from a standard terminal with **minimal path confusion**.

## Goals

1. Ensure a **machine handoff** exists; create from `machines/MACHINE_HANDOFF.example.md` if missing (ask for git identity).
2. Locate or place the project under the **PyControl** layout (ask before creating folders).
3. Run the correct OS setup script (idempotent).
4. Configure the H1 USB serial (**manual default** from `H1_HANDOFF.md` / config; optional discover).
5. Verify with `status` (read-only) → guided checks against **`H1_HANDOFF.md`**.
6. Stop and report if a **manual gate** blocks progress.

## Canonical layout

```text
PyControl/
  ALIGNMENT_HANDOFF.md
  machines/<HOSTNAME>_HANDOFF.md
  devices/H1_Lab/            ← this device
```

Preferred location: `~/PyControl` or `%USERPROFILE%\PyControl` (or machine handoff path).

**Path rule:** Never hard-code a real username in scripts or this brief. Use `~` / `%USERPROFILE%` / `<username>`.  
**Privacy scan:** Fix real homes in SETUP/AUTOMATION only; do not scrub accurate undo paths in `H1_HANDOFF.md`.

## Zip / USB (no git clone)

1. Ask the user where the unzipped `PyControl` folder is.
2. If missing, **ask permission** before creating `~/PyControl` (or `%USERPROFILE%\PyControl`) and copying/extracting into it.
3. If the user says no, stop and tell them exactly which folder to provide.

## OS detection → setup command

| OS | Command |
| --- | --- |
| macOS | `chmod +x "$DEVICE_DIR/scripts/setup_mac.sh" && "$DEVICE_DIR/scripts/setup_mac.sh" --non-interactive --device-id <H1_SERIAL>` |
| Linux | `chmod +x "$DEVICE_DIR/scripts/setup_linux.sh" && "$DEVICE_DIR/scripts/setup_linux.sh" --non-interactive --device-id <H1_SERIAL>` |
| Windows | `powershell -ExecutionPolicy Bypass -File "$DEVICE_DIR\scripts\setup_windows.ps1" -NonInteractive -DeviceId <H1_SERIAL>` |

Take `<H1_SERIAL>` from `H1_HANDOFF.md` or `config.json`.

Interactive serial choice (human present): run the script **without** `--non-interactive`.  
Discover instead of a fixed serial: `--discover` (PowerShell `-Discover`).  
Mac: `--install-deps` permits `brew install libftdi libusb`; otherwise the script stops and names the missing packages.

Scripts print `SETUP OK` (exit 0) or `SETUP INCOMPLETE` (exit 1).

## Manual gates (do not invent workarounds)

| Gate | Agent action |
| --- | --- |
| H1 off / USB unplugged | Ask user to power on and plug in, wait 10 s, retry |
| Python missing | Give OS-specific hint from SETUP.md; do not install system packages without permission |
| Mac: Homebrew missing | Point to https://brew.sh; do not install without permission |
| Linux: `libftdi1` / USB permissions | Give the `apt` and udev commands from SETUP.md; they need `sudo`, so ask |
| Windows: `status` fails after install | Explain the Zadig/WinUSB step in SETUP.md (can affect Gen5); user or IT decides |
| Gen5 open | Ask user to close it |
| User denies creating `~/PyControl` | Stop; ask for existing path |

## Verification checklist (guide the user)

Run from `DEVICE_DIR` with `.venv` active (setup script already does this):

1. `python h1_control.py discover` → lists the serial from `H1_HANDOFF.md` (read-only)
2. `python h1_control.py status` → connected; serial matches **`H1_HANDOFF.md`** (read-only)
3. **Ask before** `open` / `close` / `cycle` (tray motion)
4. **Ask before** `absorbance` (motion + plate load)
5. Optional: `python h1_gui.py` (user clicks Status)

## Idempotency

Re-running setup scripts is safe: reuse `.venv`, refresh requirements, keep `config.json`, re-apply serial options, run `status` again.

## After success

Point the human to `docs/USER_GUIDE.md`.  
Device brief: **`H1_HANDOFF.md`**.  
If aligning other devices, use the repo-root **`ALIGNMENT_HANDOFF.md`**.
