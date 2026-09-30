#!/usr/bin/env bash
# Start the MiR CLI using this project's .venv.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT"
if [[ ! -x "$ROOT/.venv/bin/python" ]]; then
  echo "Missing $ROOT/.venv/bin/python" >&2
  echo "Finish setup first (see docs/MIR_SETUP.md or run scripts/setup_mac.sh / setup_linux.sh)." >&2
  exit 1
fi
exec "$ROOT/.venv/bin/python" "$ROOT/mir_command.py" "$@"
