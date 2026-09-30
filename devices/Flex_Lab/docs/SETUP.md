# Flex_Lab — Setup Guide

Get a computer ready to run the Flex CLI.  
**Success check:** `python flex_control.py ping` prints `"event": "ping_ok"`.  
Confirm the reported robot **name** and **IP** against `FLEX_HANDOFF.md` (device-specific durable facts live there, not as hard requirements copied into every setup doc).

| Need | Where to find it |
| --- | --- |
| Robot Wi‑Fi | `FLEX_HANDOFF.md` (lab network name) |
| Flex IP | `config.example.json` / `config.json`, or `FLEX_HANDOFF.md` |
| Python | **3.9+** (3.9–3.12 preferred) |
| Project folder | `PyControl/devices/Flex_Lab/` |
| Operator / git identity | `PyControl/machines/<HOSTNAME>_HANDOFF.md` |

Scripts resolve paths from their own location (zip/USB safe). Preferred install location:

- Mac/Linux: `~/PyControl/` (or the path in your **machine handoff**)
- Windows: `%USERPROFILE%\PyControl\`

Do **not** paste another person’s `/Users/…` home path into commands. If unsure where PyControl is, ask or create `~/PyControl` with permission.

---

## Before any OS steps (manual gates)

1. Join the Flex robot Wi‑Fi (name in `FLEX_HANDOFF.md`).
2. Confirm you have the **`PyControl`** folder (USB unzip or existing tree).
3. Open a terminal in `PyControl/devices/Flex_Lab`, or run `scripts/setup_*.sh` / `.ps1` (they locate the device folder automatically).

**Machine handoff + git (agents and humans):**

1. Note this computer’s hostname.
2. If `machines/<HOSTNAME>_HANDOFF.md` is missing, copy `machines/MACHINE_HANDOFF.example.md`, ask the user for display name, git name, git email, and preferred PyControl path, then save.
3. With the user’s permission, set git identity on this computer (`git config --global user.name` / `user.email`) and record it in the machine handoff.
4. On later visits, read the machine handoff first; only re-prompt if fields are blank.

The Opentrons desktop App is **optional**. This CLI does not need it for `ping` / `run` / `transfer`.

---

## Fast path (recommended)

### Mac

```bash
cd ~/PyControl/devices/Flex_Lab   # or path from machines/<HOSTNAME>_HANDOFF.md
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

1. **Manual IP (recommended)** — keep the value from `config.json` / example, or type another  
2. **Auto-discover** — scan this subnet for an Opentrons robot (falls back to manual)

Non-interactive examples (agents; substitute IP from device handoff / config):

```bash
./scripts/setup_mac.sh --non-interactive --ip <FLEX_IP>
./scripts/setup_linux.sh --non-interactive --ip <FLEX_IP>
```

```powershell
.\scripts\setup_windows.ps1 -NonInteractive -Ip <FLEX_IP>
```

---

## Manual setup (if you prefer not to use the script)

### Shared steps (all OS)

1. Create/activate a virtual environment in `devices/Flex_Lab`.
2. `pip install -r requirements.txt`
3. Copy `config.example.json` → `config.json` if needed.
4. Set `robot_ip` (or `python flex_control.py discover --set-ip …`).
5. `python flex_control.py ping`

### Mac / Linux venv

```bash
cd ~/PyControl/devices/Flex_Lab   # or your PyControl path
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp -n config.example.json config.json
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
| `ping` fails | Wrong Wi‑Fi | Join network listed in `FLEX_HANDOFF.md` |
| `ping` fails | Wrong IP | Edit `config.json`, or `discover --set-ip …` using IP from handoff |
| `python` not found | PATH / install | Install Python 3.9+ |
| venv errors on Linux | `python3-venv` | `sudo apt install python3-venv` |
| PowerShell blocks scripts | Execution policy | Process-scoped Bypass (see above) |
| Discovery finds nothing | Isolated Wi‑Fi | Use **manual IP** |
| Git rejects commits | Identity unset | Fill machine handoff; set `user.name` / `user.email` |

---

## After setup

See **[USER_GUIDE.md](USER_GUIDE.md)**.  
Device facts: **[FLEX_HANDOFF.md](../FLEX_HANDOFF.md)**.  
Agents: **[AUTOMATION.md](AUTOMATION.md)** and repo-root `ALIGNMENT_HANDOFF.md`.
