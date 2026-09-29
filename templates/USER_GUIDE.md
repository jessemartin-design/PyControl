# __DEVICE_NAME__ — User Guide

Setup first: **SETUP.md**.

## Start a session

```bash
cd ~/PyControl/devices/__DEVICE_NAME__
source .venv/bin/activate   # Windows: .\.venv\Scripts\Activate.ps1
__PING_COMMAND__
```

## Command cheat sheet

| Goal | Command |
| --- | --- |
| Health | `__PING_COMMAND__` |
| (add rows) | (device-specific) |

## Troubleshooting

| Problem | What to check | Fix |
| --- | --- | --- |
| Health fails | Network / config host | Fix network; update config |
| Command not found | venv inactive | Activate `.venv` |
