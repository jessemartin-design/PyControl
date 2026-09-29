# __DEVICE_NAME__ — Setup Guide

Get a computer ready to run the __DEVICE_NAME__ CLI.  
**Success check:** `__PING_COMMAND__` reports a healthy connection.

| Need | Value |
| --- | --- |
| Network | `__WIFI_OR_NETWORK__` |
| Default host | `__DEFAULT_HOST__` |
| Python | **3.9+** (3.9–3.12 preferred) |
| Project folder | `PyControl/devices/__DEVICE_NAME__/` |

Preferred install location:

- Mac/Linux: `~/PyControl/`
- Windows: `%USERPROFILE%\PyControl\`

---

## Before any OS steps (manual gate)

1. Join / connect to **`__WIFI_OR_NETWORK__`**.
2. Confirm you have the **`PyControl`** folder.
3. Vendor GUIs are optional unless this device’s HANDOFF says otherwise.

---

## Fast path

### Mac

```bash
cd ~/PyControl/devices/__DEVICE_NAME__
chmod +x __SETUP_SCRIPT_MAC__
./__SETUP_SCRIPT_MAC__
```

### Linux

```bash
cd ~/PyControl/devices/__DEVICE_NAME__
chmod +x scripts/setup_linux.sh
./scripts/setup_linux.sh
```

### Windows (PowerShell)

```powershell
cd $env:USERPROFILE\PyControl\devices\__DEVICE_NAME__
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\scripts\setup_windows.ps1
```

---

## Troubleshooting

| Problem | What to check | Fix |
| --- | --- | --- |
| Health command fails | Network / host | Rejoin network; edit `config.json` |
| `python` not found | PATH / install | Install Python 3.9+ |
| venv errors on Linux | `python3-venv` | `sudo apt install python3-venv` |
| PowerShell blocks scripts | Execution policy | Process-scoped Bypass (see above) |

---

## After setup

See **USER_GUIDE.md**. Agents: **AUTOMATION.md**.
