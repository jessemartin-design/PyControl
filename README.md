# PyControl

Shared kit for lean, cross-platform **device CLIs** used in lab demos (humans or PAI).

```text
PyControl/
  README.md                 ← you are here
  ALIGNMENT_HANDOFF.md      ← upload into other device chats to align them
  templates/                ← blank docs for new devices
  devices/
    Flex_Lab/               ← Opentrons Flex (ready)
    MiR_API/                ← placeholder until migrated
    H1_Lab/                 ← Biotek Synergy H1 (ready)
```

## Preferred location on a computer

| OS | Path |
| --- | --- |
| Mac / Linux | `~/PyControl` |
| Windows | `%USERPROFILE%\PyControl` |

Sharing is by **zip / USB** (not git clone). After all devices are aligned and tested, zip this whole `PyControl` folder (exclude each device’s `.venv`).

## Devices

| Folder | Device | Status |
| --- | --- | --- |
| `devices/Flex_Lab` | Opentrons Flex | Active — use its `docs/` + `scripts/` |
| `devices/MiR_API` | MiR robot API | Placeholder — migrate via Alignment Handoff |
| `devices/H1_Lab` | Biotek Synergy H1 (USB) | Active — use its `docs/` + `scripts/` |

## New computer (after you have a zip)

1. Unzip to `~/PyControl` (or Windows equivalent). Ask an agent with `devices/<Name>/docs/AUTOMATION.md` if you want help.
2. Join that device’s Wi‑Fi / network (USB devices like H1_Lab: plug in the cable instead).
3. Run that device’s setup script under `devices/<Name>/scripts/`.
4. Confirm with the device’s ping/status command from its User Guide.

## Aligning MiR_API or H1_Lab into this tree

Open that project’s Cursor chat, upload **`ALIGNMENT_HANDOFF.md`**, and instruct the agent to follow it (including rename/path updates and guided verification). Prefer **one** PyControl folder on the machine; add device subfolders rather than creating a second kit.
