# H1_Lab — Automation Brief

Upload this file into a chat so an agent can set up and verify the H1 CLI from a standard terminal with **minimal path confusion**.

## Goals

1. Locate or place the project under the **PyControl** layout.
2. Run the correct OS setup script (idempotent).
3. Configure the H1 USB serial (**manual default** `22040106`, optional discover).
4. Verify with `status` (read-only) → guided checks.
5. Stop and report if a **manual gate** blocks progress (power/USB, missing Python, USB driver, user denied folder create).

## Canonical layout

```text
PyControl/
  ALIGNMENT_HANDOFF.md
  README.md
  templates/
  devices/
    Flex_Lab/          ← other device
    MiR_API/           ← other device
    H1_Lab/            ← this device
```

Preferred location on a machine:

| OS | Path |
| --- | --- |
| Mac / Linux | `~/PyControl` |
| Windows | `%USERPROFILE%\PyControl` |

**Path rule:** Never hard-code `/Users/jesse...` or one person’s Documents path.  
Resolve the device root as the directory that contains `h1_control.py` and `config.example.json`.  
Setup scripts live in `devices/H1_Lab/scripts/` and compute paths from their own location.

## Zip / USB (no git clone)

1. Ask the user where the unzipped `PyControl` folder is.
2. If missing, **ask permission** before creating `~/PyControl` (or `%USERPROFILE%\PyControl`) and copying/extracting into it.
3. If the user says no, stop and tell them exactly which folder to provide.

## OS detection → setup command

| OS | Command |
| --- | --- |
| macOS | `chmod +x "$DEVICE_DIR/scripts/setup_mac.sh" && "$DEVICE_DIR/scripts/setup_mac.sh" --non-interactive --device-id 22040106` |
| Linux | `chmod +x "$DEVICE_DIR/scripts/setup_linux.sh" && "$DEVICE_DIR/scripts/setup_linux.sh" --non-interactive --device-id 22040106` |
| Windows | `powershell -ExecutionPolicy Bypass -File "$DEVICE_DIR\scripts\setup_windows.ps1" -NonInteractive -DeviceId 22040106` |

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

1. `python h1_control.py discover` → lists `22040106` (read-only)
2. `python h1_control.py status` → `Connected to Synergy H1.` / `Serial: 22040106` (read-only)
3. **Ask before** `open` / `close` / `cycle` (tray motion)
4. **Ask before** `absorbance` (motion + plate load)
5. Optional: `python h1_gui.py` (user clicks Status)

## Idempotency

Re-running setup scripts is safe: reuse `.venv`, refresh requirements, keep `config.json`, re-apply serial options, run `status` again.

## After success

Point the human to `docs/USER_GUIDE.md`.  
If aligning other devices, use the repo-root **`ALIGNMENT_HANDOFF.md`**.
