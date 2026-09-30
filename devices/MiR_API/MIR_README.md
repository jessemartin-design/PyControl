# MiR_API (MiR robot REST API)

Device control package inside the shared **PyControl** tree: CLI and GUI for MiR200-class robots over the native HTTP API.

| Doc | Audience |
| --- | --- |
| [docs/MIR_SETUP.md](docs/MIR_SETUP.md) | Humans — install on Mac / Windows / Linux |
| [docs/MIR_USER_GUIDE.md](docs/MIR_USER_GUIDE.md) | Humans — run CLI commands and the GUI |
| [docs/MIR_AUTOMATION.md](docs/MIR_AUTOMATION.md) | Agents — automate setup from a terminal |
| [MIR_HANDOFF.md](MIR_HANDOFF.md) | Agents — status, durable facts, API/GUI diagnosis |

**Quick start:** run `scripts/setup_mac.sh`, `scripts/setup_linux.sh`, or `scripts/setup_windows.ps1`, then see the User Guide.

Parent kit: `../../README.md` and `../../ALIGNMENT_HANDOFF.md`.

**Safety:** only send motion when the area around the robot is clear. Physical e-stop is on the robot; the API cannot clear it.
