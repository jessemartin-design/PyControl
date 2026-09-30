# MiR_API — Setup Guide

Get a computer ready to run the MiR CLI and GUI.  
**Success check:** `python mir_command.py Status` (or `./run_cli.sh Status`) prints robot status.  
Confirm the **robot name / IP** against `MIR_HANDOFF.md`. This command only reads information; the robot does not move.

| Need | Where to find it |
| --- | --- |
| Network | Facility Wi‑Fi that reaches the robot (see `MIR_HANDOFF.md`) |
| Robot host / IP | `MIR_HANDOFF.md` / `.env.example` |
| Login | Same username/password as the MiR web UI → local `.env` only |
| Python | **3.10+** (3.11 or 3.12 preferred) |
| Project folder | `PyControl/devices/MiR_API/` |
| Operator / git identity | `PyControl/machines/<HOSTNAME>_HANDOFF.md` |

Scripts resolve paths from their own location (zip/USB safe). Preferred install location:

- Mac/Linux: `~/PyControl/` (or path in the **machine handoff**)
- Windows: `%USERPROFILE%\PyControl\`

Do **not** paste another person’s `/Users/…` path into setup commands.

**Config note:** MiR uses `.env` / `.env.example` (not `config.json`). Secrets never go in docs or git.

---

## Before any OS steps (manual gate)

1. Power on the MiR and wait until it is ready on Wi‑Fi.
2. Join the facility Wi‑Fi that can reach the robot (not only the MiR hotspot, unless that is intentional).
3. In a browser, open `http://<robot-ip>` and confirm the web UI loads (IP lives in `MIR_HANDOFF.md`).
4. Confirm you have the **`PyControl`** folder (unzipped from USB, or already on this computer).

**Machine handoff + git (agents and humans):** if `machines/<HOSTNAME>_HANDOFF.md` is missing, copy the example, ask for operator name + git name/email + preferred PyControl path, save the file, and with permission set `git config --global user.name` / `user.email`. See repo-root `ALIGNMENT_HANDOFF.md`.

---

## Fast path (recommended)

### Mac

```bash
cd ~/PyControl/devices/MiR_API   # or your actual PyControl path
chmod +x scripts/setup_mac.sh
./scripts/setup_mac.sh
```

The script creates/reuses `.venv`, installs requirements, ensures `.env`, asks for the robot IP if needed, then runs **Status**.

Non-interactive (host known; `.env` already has credentials):

```bash
./scripts/setup_mac.sh --non-interactive --ip <ROBOT_IP>
```

### Linux

```bash
sudo apt update
sudo apt install python3 python3-venv python3-pip
# GUI later: python3-tk
```

```bash
cd ~/PyControl/devices/MiR_API
chmod +x scripts/setup_linux.sh
./scripts/setup_linux.sh
```

### Windows (PowerShell)

Install Python 3.10+ from [python.org](https://www.python.org/downloads/windows/) with **Add python.exe to PATH** and Tcl/Tk enabled.

```powershell
cd $env:USERPROFILE\PyControl\devices\MiR_API
powershell -ExecutionPolicy Bypass -File .\scripts\setup_windows.ps1
```

Non-interactive:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\setup_windows.ps1 -NonInteractive -Ip <ROBOT_IP>
```

---

## Credentials (`.env`)

If the setup script created a blank `.env`, edit it:

```env
MIR_HOST=<robot-ip>
MIR_USERNAME=<web-ui-username>
MIR_PASSWORD=<web-ui-password>
MIR_VERIFY_TLS=false
```

Never commit `.env` or paste passwords into chat. Live IP and robot name: **`MIR_HANDOFF.md`**.

---

## After `SETUP OK`

Everyday commands: **[MIR_USER_GUIDE.md](MIR_USER_GUIDE.md)**.  
Agents: **[MIR_AUTOMATION.md](MIR_AUTOMATION.md)**.  
Device brief: **`../MIR_HANDOFF.md`**.

Launchers (optional; they activate `.venv` for you):

| What | Mac / Linux | Windows |
| --- | --- | --- |
| CLI | `./run_cli.sh` | `.\run_cli.bat` |
| GUI | `./run_gui.sh` | `.\run_gui.bat` |

---

## Troubleshooting

| Symptom | What to try |
| --- | --- |
| `Status` / setup fails to connect | Same Wi‑Fi as the robot? Browser open `http://<ip>`? `MIR_HOST` correct? |
| Auth / 401 | Password hash is **case-sensitive**; try the exact case set on the robot (often lowercase). Same login as the web UI. |
| `No module named '_tkinter'` (GUI) | Reinstall Python from python.org with Tcl/Tk, or on Linux install `python3-tk`. |
| Wrong folder | Work from `PyControl/devices/MiR_API`, not an old Desktop copy. |
| Stale env | Delete `.venv` and re-run the setup script. |

Optional offline tests (no robot):

```bash
.venv/bin/python -m unittest discover -s tests
```
