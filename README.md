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

Sharing is by **zip / USB**, built from git so only committed files ship (no `.venv`, local `config.json`, results, or `machines/*_HANDOFF.md`). Commit first, then from this folder:

```bash
git archive --format=zip --prefix=PyControl/ -o ../PyControl_YYYYMMDD.zip HEAD
```

Don't use Finder “Compress” or Explorer “Compressed folder” — they include personal and machine-specific files. Details: `ALIGNMENT_HANDOFF.md` → **Sharing / zip**. Recipients create their own machine handoff during setup.

Device handoffs (`*_HANDOFF.md`) do ship: they record real device facts and who did what, so share the zip with lab teammates only.

## Devices

| Folder | Device | Status |
| --- | --- | --- |
| `devices/Flex_Lab` | Opentrons Flex | Active — `FLEX_README.md`, tagged `docs/FLEX_*.md`, `FLEX_HANDOFF.md` |
| `devices/MiR_API` | MiR robot API | Active — tagged `MIR_*.md` docs + `MIR_HANDOFF.md`; Desktop backup `MiR_API_backup_20260930` |
| `devices/H1_Lab` | Biotek Synergy H1 (USB) | Active — `H1_README.md`, tagged `docs/H1_*.md`, `H1_HANDOFF.md` |

## New computer (after you have a zip)

1. Unzip to `~/PyControl` (ask before using another folder).
2. Create `machines/<HOSTNAME>_HANDOFF.md` from the example (git name/email, preferred path).
3. Connect that device’s network or USB.
4. Run `devices/<Name>/scripts/setup_…` then confirm with the User Guide health command.

## Aligning another device

Upload **`ALIGNMENT_HANDOFF.md`** into that chat. Agents should: migrate into this tree, use tagged device docs (`<TAG>_README.md`, `docs/<TAG>_SETUP.md`, …) and `<TAG>_HANDOFF.md`, scrub usernames from SETUP/AUTOMATION only, preserve accurate device-handoff history, and ensure a machine handoff exists.
