# __DEVICE_NAME__ — Setup Guide

Get a computer ready to run the __DEVICE_NAME__ CLI.  
**Success check:** `__PING_COMMAND__` reports healthy. Confirm live IDs against `__DEVICE_HANDOFF_FILE__`.

| Need | Where to find it |
| --- | --- |
| Network / link | `__DEVICE_HANDOFF_FILE__` |
| Default host / id | `__DEVICE_HANDOFF_FILE__` / `config.example.json` |
| Python | **3.9+** (3.9–3.12 preferred) |
| Project folder | `PyControl/devices/__DEVICE_NAME__/` |
| Operator / git | `machines/<HOSTNAME>_HANDOFF.md` |

Preferred install location:

- Mac/Linux: `~/PyControl/` (or machine handoff path)
- Windows: `%USERPROFILE%\PyControl\`

Never paste another person’s `/Users/…` home into commands. Ask before creating folders.

---

## Before any OS steps

1. Connect per `__DEVICE_HANDOFF_FILE__`.
2. Confirm the **`PyControl`** folder.
3. Ensure machine handoff exists (copy example; collect git identity; optional `git config --global`).
4. Vendor GUIs optional unless the device handoff says otherwise.

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
| Health fails | Network / host | See device handoff; edit `config.json` |
| `python` not found | PATH | Install Python 3.9+ |
| venv errors on Linux | `python3-venv` | `sudo apt install python3-venv` |
| Git commit identity | Machine handoff blank | Ask user; set git config |
| PowerShell blocks scripts | Execution policy | Process Bypass |

---

## After setup

See **USER_GUIDE.md**. Agents: **AUTOMATION.md**. Process: repo-root `ALIGNMENT_HANDOFF.md`.
