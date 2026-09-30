# MiR_API — User Guide

Plain instructions to control a **MiR** robot (MiR200 and similar) from a terminal or a button window.  
Setup first: **[MIR_SETUP.md](MIR_SETUP.md)**.

---

## Words you will see

| Term | Plain meaning |
| --- | --- |
| **MiR** | The mobile robot (this lab: see `MIR_HANDOFF.md`) |
| **CLI** | Terminal commands via `mir_command.py` / `run_cli` |
| **GUI** | Desktop window (`python -m gui` / `run_gui`) |
| **`.venv`** | Private Python toolbox for this project |
| **`.env`** | Local secrets file (host + web UI login) — never commit |
| **Draft queue** | List of positions/missions the GUI will run in order |

---

## Start a session (every time)

1. Confirm the robot is on and reachable (browser: `http://<robot-ip>` from `MIR_HANDOFF.md`).
2. Open a terminal.
3. Go to the device folder and activate the virtual environment **or** use a launcher.

**Mac / Linux**

```bash
cd ~/PyControl/devices/MiR_API   # use your real PyControl path if different
source .venv/bin/activate
python mir_command.py Status
```

Or: `./run_cli.sh Status`

**Windows (PowerShell)**

```powershell
cd $env:USERPROFILE\PyControl\devices\MiR_API
.\.venv\Scripts\Activate.ps1
python mir_command.py Status
```

Or: `.\run_cli.bat Status`

Done when you see a connected banner and status lines (robot name should match **`MIR_HANDOFF.md`**).

---

## Command cheat sheet

| Goal | Command | Moves the robot? |
| --- | --- | --- |
| Health / state | `python mir_command.py Status` | No |
| List named positions | `python mir_command.py ListPositions` | No |
| List missions | `python mir_command.py ListMissions` | No |
| Interactive shell | `python mir_command.py` then type commands | Only if you send motion |
| Go to a position | `python mir_command.py GoToPosition <name>` | **Yes** |
| Run a mission | `python mir_command.py RunMission <name>` | **Yes** |
| Help | `python mir_command.py` → type `Help` | No |
| GUI | `python -m gui` or `./run_gui.sh` | Only when you press Start |

Override host for one run: `python mir_command.py --host <ip> Status`

---

## GUI (typical flow)

1. Start: `./run_gui.sh` (Mac/Linux) or `.\run_gui.bat` (Windows).
2. Refresh catalogs (positions / missions).
3. Add items to the **draft** queue; reorder if needed.
4. **Ask before Start** — area around the robot must be clear.
5. Use **Pause** / **Stop** as needed.

Closing the GUI while a **Charge** mission is active may prompt before aborting Charge — see `PROJECT_KNOWLEDGE.md` if you need the details.

---

## Safety

- Only send motion (`GoToPosition`, `RunMission`, GUI **Start**) when the area is clear.
- Physical e-stop must be cleared on the robot; the API cannot clear it.
- Never put passwords in chat, commits, or shared docs.

---

## More detail

| Doc | Use when |
| --- | --- |
| [MIR_SETUP.md](MIR_SETUP.md) | Install / `SETUP OK` |
| [MIR_AUTOMATION.md](MIR_AUTOMATION.md) | Agent-driven setup |
| [PROJECT_KNOWLEDGE.md](PROJECT_KNOWLEDGE.md) | API quirks, GUI behavior, endpoints |
| [`../MIR_HANDOFF.md`](../MIR_HANDOFF.md) | Robot name, IP, Wi‑Fi, migration / undo |
