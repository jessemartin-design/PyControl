# H1_Lab — Setup Guide

Get a computer ready to run the H1 CLI and GUI.  
**Success check:** `python h1_control.py status` prints a connected Synergy H1 message.  
Confirm the **serial** against `H1_HANDOFF.md`. This command only reads information; the tray does not move.

| Need | Where to find it |
| --- | --- |
| Connection | **USB** from H1 to this computer |
| H1 USB serial | `H1_HANDOFF.md` / `config.example.json` |
| Python | **3.9+** |
| Project folder | `PyControl/devices/H1_Lab/` |
| Operator / git identity | `PyControl/machines/<HOSTNAME>_HANDOFF.md` |

Scripts resolve paths from their own location (zip/USB safe). Preferred install location:

- Mac/Linux: `~/PyControl/` (or path in the **machine handoff**)
- Windows: `%USERPROFILE%\PyControl\`

Do **not** paste another person’s `/Users/…` path into setup commands.

---

## Before any OS steps (manual gate)

1. Power on the H1 and wait ~10 seconds.
2. Plug the H1's USB cable into **this** computer.
3. Close **Gen5** or any other program that talks to the H1 (only one program can use it at a time).
4. Confirm you have the **`PyControl`** folder (unzipped from USB, or copied).

**Machine handoff + git (agents and humans):** if `machines/<HOSTNAME>_HANDOFF.md` is missing, copy the example, ask for operator name + git name/email + preferred PyControl path, save the file, and with permission set `git config --global user.name` / `user.email`. See repo-root `ALIGNMENT_HANDOFF.md`.

---

## Fast path (recommended)

### Mac

Needs [Homebrew](https://brew.sh). The script checks for the USB libraries (`libftdi`, `libusb`) and asks before installing them.

```bash
cd ~/PyControl/devices/H1_Lab   # or your actual PyControl path
chmod +x scripts/setup_mac.sh
./scripts/setup_mac.sh
```

### Linux (not yet verified on hardware)

Install the system pieces first (Debian/Ubuntu names):

```bash
sudo apt update
sudo apt install python3 python3-venv python3-pip libftdi1-2 libusb-1.0-0
```

Then:

```bash
cd ~/PyControl/devices/H1_Lab
chmod +x scripts/setup_linux.sh
./scripts/setup_linux.sh
```

Non-root users usually need permission to open the USB device. One common fix (then unplug/replug the H1):

```bash
echo 'SUBSYSTEM=="usb", ATTR{idVendor}=="0403", ATTR{idProduct}=="6001", MODE="0666"' | sudo tee /etc/udev/rules.d/99-h1-ftdi.rules
sudo udevadm control --reload-rules && sudo udevadm trigger
```

### Windows (PowerShell, not yet verified on hardware)

```powershell
cd $env:USERPROFILE\PyControl\devices\H1_Lab
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\scripts\setup_windows.ps1
```

Windows usually needs extra USB setup before `status` works, because the Python USB library (`libftdi`) cannot use the default FTDI driver. Typical fix: use [Zadig](https://zadig.akeo.ie/) to switch the H1's FTDI device (VID `0403`, PID `6001`) to the **WinUSB** driver. Note that this can stop Gen5 from seeing the H1 on that PC until you switch the driver back. Ask IT if you are unsure.

During setup you will be asked:

1. **Manual serial (recommended)** — press Enter to keep `22040106`, or type another serial
2. **Auto-discover** — list FTDI USB devices plugged into this computer and save the serial if exactly one is found

Non-interactive examples (agents / automation):

```bash
./scripts/setup_mac.sh --non-interactive --device-id 22040106
./scripts/setup_linux.sh --non-interactive --device-id 22040106
```

```powershell
.\scripts\setup_windows.ps1 -NonInteractive -DeviceId 22040106
```

Mac only: add `--install-deps` to let the script run `brew install libftdi libusb` without asking.

---

## Manual setup (if you prefer not to use the script)

### Shared steps (all OS)

1. Create/activate a virtual environment in `devices/H1_Lab`.
2. `pip install -r requirements.txt`
3. Copy `config.example.json` → `config.json` if needed.
4. Set `ftdi_device_id` in `config.json` (or `python h1_control.py discover --set-device-id 22040106`).
5. `python h1_control.py status`

### Mac venv

```bash
cd /path/to/PyControl/devices/H1_Lab
python3 -m venv .venv
echo 'export DYLD_LIBRARY_PATH="$(brew --prefix)/opt/libftdi/lib:$(brew --prefix)/lib${DYLD_LIBRARY_PATH:+:$DYLD_LIBRARY_PATH}"' >> .venv/bin/activate
source .venv/bin/activate
pip install -r requirements.txt
cp -n config.example.json config.json
python h1_control.py status
```

The `DYLD_LIBRARY_PATH` line tells Python where Homebrew put the USB libraries.

### Linux venv

```bash
cd /path/to/PyControl/devices/H1_Lab
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp -n config.example.json config.json
python h1_control.py status
```

### Windows venv (PowerShell)

```powershell
cd $env:USERPROFILE\PyControl\devices\H1_Lab
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item config.example.json config.json -Force
python h1_control.py status
```

---

## Settings

`config.json` (local, not committed):

| Key | Meaning | Default |
| --- | --- | --- |
| `ftdi_device_id` | H1 USB serial | `22040106` |
| `results_dir` | Where absorbance CSV/JSON files go (relative to the device folder) | `results` |

Serial lookup order: `--device-id` flag → `H1_FTDIDEVICE_ID` environment variable → `config.json` → legacy `.env` (only if there is no `config.json`) → `22040106`.

---

## Troubleshooting

| Problem | What to check | Fix |
| --- | --- | --- |
| `status` fails / device not found | H1 power, USB cable, port | Power on, reseat cable, wait 10 s, retry |
| `discover` finds nothing | Same as above; Windows driver; Linux permissions | See Windows (Zadig/WinUSB) or Linux (udev) notes above |
| `status` fails, device busy | Gen5 or another script is open | Close the other program; only one controller at a time |
| Wrong instrument / serial | `ftdi_device_id` in `config.json` | `python h1_control.py discover`, then `discover --set-device-id <serial>` |
| Mac: `libftdi` / library not found | Homebrew libs or `DYLD_LIBRARY_PATH` | `brew install libftdi libusb`; re-run `setup_mac.sh` (it re-adds the line) |
| `python` / `python3` not found | Python not installed or not on PATH | Install Python 3.9+; on Windows tick “Add python.exe to PATH”, reopen terminal |
| `ensurepip` / `venv` errors on Linux | Missing `python3-venv` | `sudo apt install python3-venv` |
| PowerShell blocks scripts | Execution policy | `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` |
| GUI will not open on Linux | tkinter missing | `sudo apt install python3-tk` |

---

## After setup

See **[USER_GUIDE.md](USER_GUIDE.md)** for everyday commands.  
Agents: see **[AUTOMATION.md](AUTOMATION.md)**.
