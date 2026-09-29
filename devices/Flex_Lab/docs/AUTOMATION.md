# Flex_Lab — Automation Brief

Upload this file into a chat so an agent can set up and verify the Flex CLI from a standard terminal with **minimal path confusion**.

## Goals

1. Locate or place the project under the **PyControl** layout.
2. Run the correct OS setup script (idempotent).
3. Configure Flex IP (**manual default**, optional discover).
4. Verify with `ping` → guided status check.
5. Stop and report if a **manual gate** blocks progress (Wi‑Fi, missing Python, user denied folder create).

## Canonical layout

```text
PyControl/
  ALIGNMENT_HANDOFF.md
  README.md
  templates/
  devices/
    Flex_Lab/          ← this device
    MiR_API/           ← other device (may be empty until migrated)
    H1_Lab/            ← other device (may be empty until migrated)
```

Preferred location on a machine:

| OS | Path |
| --- | --- |
| Mac / Linux | `~/PyControl` |
| Windows | `%USERPROFILE%\PyControl` |

**Path rule:** Never hard-code `/Users/jesse...` or one person’s Documents path.  
Resolve the device root as the directory that contains `flex_control.py` and `config.example.json`.  
Setup scripts live in `devices/Flex_Lab/scripts/` and compute paths from `__file__` / `$PSScriptRoot`.

## Zip / USB (no git clone)

This project is shared by **zip or USB**, not git clone.

1. Ask the user where the unzipped `PyControl` folder is.
2. If missing, **ask permission** before creating `~/PyControl` (or `%USERPROFILE%\PyControl`) and copying/extracting into it.
3. If the user says no, stop and tell them exactly which folder to provide.

## OS detection → setup command

Working directory may be anywhere; invoke scripts by absolute path once `DEVICE_DIR` is known.

| OS | Command |
| --- | --- |
| macOS | `chmod +x "$DEVICE_DIR/scripts/setup_mac.sh" && "$DEVICE_DIR/scripts/setup_mac.sh" --non-interactive --ip 10.14.19.180` |
| Linux | `chmod +x "$DEVICE_DIR/scripts/setup_linux.sh" && "$DEVICE_DIR/scripts/setup_linux.sh" --non-interactive --ip 10.14.19.180` |
| Windows | `powershell -File "$DEVICE_DIR\scripts\setup_windows.ps1" -NonInteractive -Ip 10.14.19.180` |

Interactive IP choice (human present): run the script **without** `--non-interactive` so they can pick manual vs discover.

Optional discover instead of fixed IP:

```bash
"$DEVICE_DIR/scripts/setup_mac.sh" --non-interactive --discover
```

## Manual gates (do not invent workarounds)

| Gate | Agent action |
| --- | --- |
| Not on robot Wi‑Fi | Ask user to join `optrn-nyc1-robotics`, then retry |
| Python missing | Give OS-specific install hint from SETUP.md; do not install system packages without permission |
| User denies creating `~/PyControl` | Stop; ask for existing path |
| `ping` fails after setup | Report Wi‑Fi + `robot_ip`; try browser health URL; do not start liquid-handling runs |

**Do not** auto-launch the Opentrons App as part of CLI setup.

## Verification checklist (guide the user)

Run from `DEVICE_DIR` with `.venv` active (setup script already does this):

1. `python flex_control.py ping` → expect `ping_ok` / `Chemelian`
2. `python flex_control.py status` → expect reachable + right-mount P50
3. `python flex_control.py protocols` → list stored protocols
4. Ask before any `run` / `transfer` (motion / liquid)

## Idempotency

Re-running setup scripts is safe: reuse `.venv`, refresh requirements, re-apply IP options, ping again.

## After success

Point the human to `docs/USER_GUIDE.md`.  
If aligning other devices (MiR_API, H1_Lab), use the repo-root **`ALIGNMENT_HANDOFF.md`**.
