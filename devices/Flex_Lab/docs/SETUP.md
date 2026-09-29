# Flex_Lab — Setup Guide

Get a computer ready to run the Flex CLI.  
**Success check:** `python flex_control.py ping` prints `"event": "ping_ok"` and the robot name (`Chemelian`).

| Need | Value |
| --- | --- |
| Wi‑Fi | `optrn-nyc1-robotics` (same network as the Flex) |
| Default Flex IP | `10.14.19.180` |
| Python | **3.9+** (3.9–3.12 preferred) |
| Project folder | `PyControl/devices/Flex_Lab/` |

Scripts resolve paths from their own location, so a USB/zip copy works even if the drive letter or home folder differs. Preferred install location on a new machine:

- Mac/Linux: `~/PyControl/`
- Windows: `%USERPROFILE%\PyControl\`

---

## Before any OS steps (manual gate)

1. Join Wi‑Fi **`optrn-nyc1-robotics`**.
2. Confirm you have the **`PyControl`** folder (unzipped from USB, or this repo renamed/moved to `PyControl`).
3. Open a terminal **inside** `PyControl/devices/Flex_Lab` *or* run the setup script from `scripts/` (it finds the device folder automatically).

The Opentrons desktop App is **optional** (calibration / deck checks only). This CLI does not need it for `ping` / `run` / `transfer`.

---

## Fast path (recommended)

### Mac

```bash
cd ~/PyControl/devices/Flex_Lab   # or your actual PyControl path
chmod +x scripts/setup_mac.sh
./scripts/setup_mac.sh
```

### Linux

```bash
cd ~/PyControl/devices/Flex_Lab
chmod +x scripts/setup_linux.sh
./scripts/setup_linux.sh
```

If `python3-venv` is missing (Debian/Ubuntu):

```bash
sudo apt update
sudo apt install python3 python3-venv python3-pip
```

### Windows (PowerShell)

```powershell
cd $env:USERPROFILE\PyControl\devices\Flex_Lab
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\scripts\setup_windows.ps1
```

During setup you will be asked:

1. **Manual IP (recommended)** — press Enter to keep `10.14.19.180`, or type another IP  
2. **Auto-discover** — scan this Wi‑Fi subnet for an Opentrons robot (falls back to manual if none/ambiguous)

Non-interactive examples (agents / automation):

```bash
./scripts/setup_mac.sh --non-interactive --ip 10.14.19.180
./scripts/setup_linux.sh --non-interactive --ip 10.14.19.180
```

```powershell
.\scripts\setup_windows.ps1 -NonInteractive -Ip 10.14.19.180
```

---

## Manual setup (if you prefer not to use the script)

### Shared steps (all OS)

1. Create/activate a virtual environment in `devices/Flex_Lab`.
2. `pip install -r requirements.txt`
3. Copy `config.example.json` → `config.json` if needed.
4. Set `robot_ip` in `config.json` (or `python flex_control.py discover --set-ip ...`).
5. `python flex_control.py ping`

### Mac / Linux venv

```bash
cd /path/to/PyControl/devices/Flex_Lab
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp -n config.example.json config.json
python flex_control.py ping
```

### Windows venv (Command Prompt)

```bat
cd %USERPROFILE%\PyControl\devices\Flex_Lab
python -m venv .venv
.venv\Scripts\activate.bat
pip install -r requirements.txt
copy /Y config.example.json config.json
python flex_control.py ping
```

### Windows venv (PowerShell)

```powershell
cd $env:USERPROFILE\PyControl\devices\Flex_Lab
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item config.example.json config.json -Force
python flex_control.py ping
```

---

## Troubleshooting

| Problem | What to check | Fix |
| --- | --- | --- |
| `ping` fails / connection error | Wrong Wi‑Fi | Join `optrn-nyc1-robotics` |
| `ping` fails | Wrong IP | Edit `config.json` `robot_ip`, or run `python flex_control.py discover --set-ip 10.14.19.180` |
| `python` / `python3` not found | Python not installed or not on PATH | Install Python 3.9+; on Windows tick “Add to PATH” |
| `ensurepip` / `venv` errors on Linux | Missing `python3-venv` | `sudo apt install python3-venv` |
| PowerShell blocks scripts | Execution policy | `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` |
| Discovery finds nothing | Guest Wi‑Fi / isolation / different subnet | Use **manual IP** |
| Browser test | API reachable? | Open `http://10.14.19.180:31950/health` |

---

## After setup

See **[USER_GUIDE.md](USER_GUIDE.md)** for everyday commands.  
Agents: see **[AUTOMATION.md](AUTOMATION.md)**.
