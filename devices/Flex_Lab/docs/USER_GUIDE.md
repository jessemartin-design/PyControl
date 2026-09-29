# Flex_Lab — User Guide

Plain instructions to start the CLI and run commands.  
Setup first: **[SETUP.md](SETUP.md)**.

---

## Start a session (every time)

1. Join Wi‑Fi **`optrn-nyc1-robotics`**.
2. Open a terminal.
3. Go to the device folder and activate the virtual environment.

**Mac / Linux**

```bash
cd ~/PyControl/devices/Flex_Lab   # use your real PyControl path if different
source .venv/bin/activate
```

**Windows (PowerShell)**

```powershell
cd $env:USERPROFILE\PyControl\devices\Flex_Lab
.\.venv\Scripts\Activate.ps1
```

4. Confirm the robot:

```bash
python flex_control.py ping
```

Done when you see `"event": "ping_ok"` and name `Chemelian`.

---

## Command cheat sheet

All commands print **one JSON object per line**.

| Goal | Command |
| --- | --- |
| Health check | `python flex_control.py ping` |
| Status + pipette + current run | `python flex_control.py status` |
| Deck fixtures / slots | `python flex_control.py deck` |
| List protocols on robot | `python flex_control.py protocols` |
| List recent runs | `python flex_control.py runs` |
| Scan LAN for Flex (optional) | `python flex_control.py discover` |
| Save a known IP | `python flex_control.py discover --set-ip 10.14.19.180` |
| Upload a protocol file | `python flex_control.py upload protocols/demo_transfer.py` |
| Run a stored protocol by name | `python flex_control.py run "Demo"` |
| Run without waiting | `python flex_control.py run "Demo" --no-wait` |
| Pause / play / stop | `python flex_control.py pause <run_id>` / `play` / `stop` |
| Wait until finished | `python flex_control.py wait <run_id>` |
| Demo transfer | `python flex_control.py transfer --source A1 --dest B1 --volume 10` |
| Emit choreography signal | `python flex_control.py signal emit flex_done --payload status=ok` |
| Wait for signal | `python flex_control.py signal wait start_transfer --timeout 300` |

### Transfer defaults (change flags if your deck differs)

| Item | Default |
| --- | --- |
| Plate slot | `C2` |
| Tip rack slot | `B2` |
| Trash | `A3` (in protocol) |
| Pipette | Flex 50 µL single, **right** mount |

Example with slots:

```bash
python flex_control.py transfer \
  --plate-slot C2 \
  --tiprack-slot B2 \
  --source A1 \
  --dest B1 \
  --volume 10
```

### Runtime parameters on any protocol

```bash
python flex_control.py run "Flex Lab Demo Transfer" \
  --param plate_slot=C2 \
  --param source_well=A1 \
  --param dest_well=B1 \
  --param volume_ul=10
```

---

## Choreography with another system (PAI / arm)

Signals are files under `signals/` in this device folder.

**Terminal A (Flex)**

```bash
python flex_control.py signal wait start_transfer --timeout 300
python flex_control.py transfer --source A1 --dest B1 --volume 10
python flex_control.py signal emit flex_done --payload status=ok
```

**Terminal B (other system)**

```bash
python flex_control.py signal emit start_transfer
python flex_control.py signal wait flex_done --timeout 600
```

---

## Troubleshooting (everyday use)

| Problem | What to check | Fix |
| --- | --- | --- |
| `ping` fails | Wi‑Fi / IP | Rejoin robot Wi‑Fi; `discover --set-ip ...` |
| `run` / `transfer` errors | Door, deck, tips, pipette | Clear deck path; match labware to protocol |
| Wrong protocol | Name vs id | `protocols` then use exact `protocolName` or id |
| Command not found: `python` | venv not active | Activate `.venv` again |
| Want another config file | — | `python flex_control.py --config /path/to.json ping` |

---

## Safety for demos

- Close the Flex door; keep the workspace clear before motion.
- Confirm tip rack, plate, and pipette match the protocol.
- Use `pause` / `stop` if something looks wrong.
