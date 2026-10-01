# H1_Lab — User Guide

Plain instructions to control the **BioTek Synergy H1** plate reader from a terminal or a button window.  
Setup first: **[H1_SETUP.md](H1_SETUP.md)**. You do not need Gen5 for these tools.

---

## Words you will see

| Term | Plain meaning |
| --- | --- |
| **H1** | The Synergy H1 plate reader on the bench |
| **Tray** | The sliding shelf that holds the plate. **Open** = out; **close** = pulled in |
| **Terminal** | The text window where you type commands (Terminal on Mac/Linux, PowerShell on Windows) |
| **`.venv`** | A private Python toolbox for this project, so installs don't affect the rest of the computer |
| **CLI** | Commands you type: `h1_control.py` |
| **GUI** | The button window: `h1_gui.py` (it runs the CLI for you) |
| **Always-on computer** | The lab computer plugged into the H1 over USB |
| **RDP** | Remote Desktop: using another computer's screen and keyboard over the network |

---

## Start a session (every time)

1. Power on the H1; confirm its USB cable is in this computer.
2. Open a terminal.
3. Go to the device folder and activate the virtual environment.

**Mac / Linux**

```bash
cd ~/PyControl/devices/H1_Lab   # use your real PyControl path if different
source .venv/bin/activate
```

**Windows (PowerShell)**

```powershell
cd $env:USERPROFILE\PyControl\devices\H1_Lab
.\.venv\Scripts\Activate.ps1
```

4. Confirm the instrument (read-only, no motion):

```bash
python h1_control.py status
```

Done when you see `Connected to Synergy H1.` and `Serial: 22040106`.

---

## Command cheat sheet

| Goal | Command | Moves the tray? |
| --- | --- | --- |
| Health check (serial, firmware, temperature) | `python h1_control.py status` | No |
| List H1 USB devices on this computer | `python h1_control.py discover` | No |
| Save a known serial | `python h1_control.py discover --set-device-id 22040106` | No |
| Open tray | `python h1_control.py open` | Yes |
| Close tray | `python h1_control.py close` | Yes |
| Open then close | `python h1_control.py cycle` | Yes |
| Absorbance read (prompts you to load plate) | `python h1_control.py absorbance --wavelength 600` | Yes |
| Several reads in a row, tray stays closed | `python h1_control.py absorbance --wavelength 600 --repeats 3` | Yes |
| Plate already on open tray | `python h1_control.py absorbance --wavelength 600 --already-loaded` | Yes |
| Button window | `python h1_gui.py` | Only when you click |
| Use another settings file | `python h1_control.py --config /path/to.json status` | No |

### Absorbance

1. The script opens the tray and asks you to place the plate.
2. Press Enter; the tray closes, reads, and opens again.
3. Results are saved in `results/` as a pair: **`.csv`** (opens in Excel) and **`.json`** (for software), e.g. `results/h1_absorbance_600nm_result.csv`.

Plate used here: Corning Axygen **P-96-450V-C-S** (software name `Cor_Axy_96_wellplate_500uL_Ub`). These reads are for demos, not research-grade assays.

### GUI

```bash
python h1_gui.py
```

Suggested first run: **Status** → **Open tray** → **Close tray** → **Absorbance** (follow the on-screen confirmations). If a button fails, run the same action in the terminal to see the full message.

---

## Who can control the H1? (local, LAN, RDP)

The H1 is controlled only from the **always-on computer** that its USB cable is plugged into.

| Where you are | How |
| --- | --- |
| At the always-on computer | Use the commands above directly |
| Another computer on the same network | **Remote Desktop (RDP)** into the always-on computer, then use the commands inside that session |
| Another city | Same as above: RDP into the always-on computer (via VPN if IT requires) |

Do not expose the H1 control computer directly to the public internet. Hub / network-gateway ideas (if any) live in the local gitignored PAI_Lab backup under `PyControl/backups/`, not as an active sibling of this folder.

---

## Troubleshooting (everyday use)

| Problem | What to check | Fix |
| --- | --- | --- |
| `status` fails | Power, USB, other programs | Power on, reseat USB, close Gen5; retry |
| Tray does not move | Did `status` work? | Fix `status` first; keep the tray path clear |
| Command not found: `python` | venv not active | Activate `.venv` again (Start a session, step 3) |
| GUI button errors | Full message | Run the same command in the terminal |
| Can't find results | `results_dir` in `config.json` | Default is `results/` in this folder |
| Remote colleague can't connect | Connection method | RDP into the always-on computer |

---

## Safety for demos

- Keep hands clear when the tray moves.
- Don't unplug USB during a read unless recovering from a fault.
- Only one program should control the H1 at a time.
