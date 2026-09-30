# Flex_Lab — Automation Brief

Upload this file into a chat so an agent can set up and verify the Flex CLI from a standard terminal with **minimal path confusion**.

## Goals

1. Ensure a **machine handoff** exists (`machines/<HOSTNAME>_HANDOFF.md`); create from the example if missing (ask user for git identity and paths).
2. Locate or place the project under the **PyControl** layout (ask before creating folders).
3. Run the correct OS setup script (idempotent).
4. Configure Flex IP (**manual default** from device handoff / config; optional discover).
5. Verify with `ping` → guided status check (compare name/IP to **`FLEX_HANDOFF.md`**).
6. Stop and report if a **manual gate** blocks progress.

## Canonical layout

```text
PyControl/
  ALIGNMENT_HANDOFF.md
  machines/<HOSTNAME>_HANDOFF.md    ← local; gitignored
  devices/Flex_Lab/                 ← this device
```

Preferred docs paths: `~/PyControl` or `%USERPROFILE%\PyControl` (override from machine handoff).

**Path rule:** Never hard-code a real OS username into scripts or this brief. Use `~` / `%USERPROFILE%` / `<username>`.  
Resolve device root as the directory with `flex_control.py` + `config.example.json`.

## Privacy scan (do this every time)

Search SETUP/AUTOMATION (this device and any project being aligned) for real `/Users/<person>` homes. Fix those docs.  
**Do not** scrub accurate backup/undo paths inside `FLEX_HANDOFF.md` or other `<TAG>_HANDOFF.md` files.

## Zip / USB

1. Ask where `PyControl` is.
2. If missing, **ask permission** before creating the preferred path from the machine handoff (default `~/PyControl`).
3. If the user declines, stop and request an existing path.

## Machine handoff + git

1. Detect hostname; open or create `machines/<HOSTNAME>_HANDOFF.md`.
2. If git name/email blank, ask the user; write them into the machine handoff.
3. With permission: `git config --global user.name` / `user.email`.
4. Reuse the file on later runs (agent “memory” for this PC).

## OS detection → setup

| OS | Command |
| --- | --- |
| macOS | `chmod +x "$DEVICE_DIR/scripts/setup_mac.sh" && "$DEVICE_DIR/scripts/setup_mac.sh" --non-interactive --ip <FLEX_IP>` |
| Linux | same with `setup_linux.sh` |
| Windows | `powershell -File "$DEVICE_DIR\scripts\setup_windows.ps1" -NonInteractive -Ip <FLEX_IP>` |

Take `<FLEX_IP>` from `FLEX_HANDOFF.md` or `config.json`. Interactive setups: omit `--non-interactive` for manual vs discover prompts.

## Manual gates

| Gate | Agent action |
| --- | --- |
| Wrong / unknown Wi‑Fi | Point user to SSID in `FLEX_HANDOFF.md` |
| Python missing | SETUP.md hints; ask before installing packages |
| User denies creating PyControl | Stop; ask for path |
| `ping` fails | Wi‑Fi + IP from handoff/config; no motion commands |
| Machine handoff refused | Explain commits/setup memory will be painful; retry ask |

**Do not** auto-launch the Opentrons App for CLI setup.

## Verification checklist

1. `python flex_control.py ping` → `ping_ok`
2. Robot name / model match **`FLEX_HANDOFF.md`**
3. `python flex_control.py status` → reachable + expected pipette (see handoff)
4. `python flex_control.py protocols` (optional list)
5. Ask before `run` / `transfer`

## Idempotency

Re-run setup safely: reuse `.venv`, refresh requirements, re-apply IP, ping again.

## After success

Point humans to `docs/USER_GUIDE.md` and `FLEX_HANDOFF.md`.  
Cross-device process: repo-root **`ALIGNMENT_HANDOFF.md`**.
