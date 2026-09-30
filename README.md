# PyControl

Shared kit for lean, cross-platform **device CLIs** used in lab demos (humans or PAI).

```text
PyControl/
  README.md
  ALIGNMENT_HANDOFF.md       ← upload into other device chats
  machines/                  ← per-computer operator/git facts (local *_HANDOFF.md gitignored)
  templates/
  devices/
    Flex_Lab/
    MiR_API/
    H1_Lab/
```

## Preferred location on a computer

| OS | Path |
| --- | --- |
| Mac / Linux | `~/PyControl` (or path in `machines/<HOSTNAME>_HANDOFF.md`) |
| Windows | `%USERPROFILE%\PyControl` |

Sharing is by **zip / USB**. Exclude each device’s `.venv` and do not rely on gitignored `machines/*_HANDOFF.md` files traveling with the zip (recipients create their own machine handoff during setup).

## Devices

| Folder | Device | Status |
| --- | --- | --- |
| `devices/Flex_Lab` | Opentrons Flex | Active — `docs/` + `FLEX_HANDOFF.md` |
| `devices/MiR_API` | MiR robot API | Placeholder — migrate via Alignment |
| `devices/H1_Lab` | Biotek Synergy H1 (USB) | Active — `docs/` + `H1_HANDOFF.md` |

## New computer (after you have a zip)

1. Unzip to `~/PyControl` (ask before using another folder).
2. Create `machines/<HOSTNAME>_HANDOFF.md` from the example (git name/email, preferred path).
3. Connect that device’s network or USB.
4. Run `devices/<Name>/scripts/setup_…` then confirm with the User Guide health command.

## Aligning another device

Upload **`ALIGNMENT_HANDOFF.md`** into that chat. Agents should: migrate into this tree, use `<TAG>_HANDOFF.md`, scrub usernames from SETUP/AUTOMATION only, preserve accurate device-handoff history, and ensure a machine handoff exists.
