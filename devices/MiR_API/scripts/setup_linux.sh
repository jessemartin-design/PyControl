#!/usr/bin/env bash
# Idempotent MiR_API setup for Linux.
# Safe to re-run. Resolves paths from this script's location (zip/USB friendly).
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DEVICE_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
PYCONTROL_ROOT="$(cd "${DEVICE_DIR}/../.." && pwd)"
NON_INTERACTIVE=0
SET_IP=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --non-interactive) NON_INTERACTIVE=1; shift ;;
    --ip|--host) SET_IP="${2:-}"; shift 2 ;;
    -h|--help)
      echo "Usage: $0 [--non-interactive] [--ip ROBOT_IP]"
      echo "  --ip / --host  set MIR_HOST in .env before the health check"
      exit 0
      ;;
    *) echo "Unknown option: $1"; exit 2 ;;
  esac
done

echo "PyControl root: ${PYCONTROL_ROOT}"
echo "Device folder:  ${DEVICE_DIR}"

if [[ ! -f "${DEVICE_DIR}/mir_command.py" ]]; then
  echo "ERROR: mir_command.py not found in ${DEVICE_DIR}"
  exit 1
fi

pick_python() {
  for candidate in python3.12 python3.11 python3.10 python3; do
    if command -v "${candidate}" >/dev/null 2>&1; then
      echo "${candidate}"
      return 0
    fi
  done
  return 1
}

PYTHON_BIN="$(pick_python || true)"
if [[ -z "${PYTHON_BIN}" ]]; then
  echo "ERROR: Python 3 not found. On Debian/Ubuntu: sudo apt install python3 python3-venv python3-pip"
  exit 1
fi

PY_VERSION="$("${PYTHON_BIN}" -c 'import sys; print("%d.%d" % sys.version_info[:2])')"
"${PYTHON_BIN}" -c 'import sys; raise SystemExit(0 if sys.version_info >= (3, 10) else 1)' || {
  echo "ERROR: Need Python 3.10+. Found ${PY_VERSION} (${PYTHON_BIN})"
  exit 1
}
echo "Using ${PYTHON_BIN} (${PY_VERSION})"

"${PYTHON_BIN}" -c 'import venv' 2>/dev/null || {
  echo "ERROR: python3-venv missing. On Debian/Ubuntu: sudo apt install python3-venv"
  exit 1
}

cd "${DEVICE_DIR}"

if [[ ! -d .venv ]]; then
  echo "Creating virtual environment (.venv)..."
  "${PYTHON_BIN}" -m venv .venv
else
  echo "Virtual environment already exists — reusing .venv"
fi

# shellcheck disable=SC1091
source .venv/bin/activate
python -m pip install --upgrade pip >/dev/null
pip install -r requirements.txt

chmod +x run_cli.sh run_gui.sh mir_command.py 2>/dev/null || true

if [[ ! -f .env ]]; then
  cp .env.example .env
  echo "Created .env from .env.example — edit MIR_USERNAME / MIR_PASSWORD (and MIR_HOST if needed)."
fi

set_mir_host() {
  local host="$1"
  if grep -q '^MIR_HOST=' .env; then
    local tmp
    tmp="$(mktemp)"
    awk -v h="${host}" 'BEGIN{done=0} /^MIR_HOST=/{print "MIR_HOST=" h; done=1; next} {print} END{if(!done) print "MIR_HOST=" h}' .env > "${tmp}"
    mv "${tmp}" .env
  else
    echo "MIR_HOST=${host}" >> .env
  fi
  echo "Set MIR_HOST=${host} in .env"
}

if [[ -n "${SET_IP}" ]]; then
  set_mir_host "${SET_IP}"
elif [[ "${NON_INTERACTIVE}" -eq 0 ]]; then
  DEFAULT_HOST="$(grep -E '^MIR_HOST=' .env | head -n1 | cut -d= -f2-)"
  DEFAULT_HOST="${DEFAULT_HOST:-}"
  echo ""
  echo "Robot IP / host (see MIR_HANDOFF.md for the lab default)."
  if [[ -n "${DEFAULT_HOST}" ]]; then
    read -r -p "Enter MIR_HOST [${DEFAULT_HOST}]: " TYPED
    TYPED="${TYPED:-$DEFAULT_HOST}"
  else
    read -r -p "Enter MIR_HOST: " TYPED
  fi
  if [[ -n "${TYPED}" ]]; then
    set_mir_host "${TYPED}"
  fi
fi

echo ""
echo "Verifying connection (read-only Status; the robot does not move)..."
echo "Confirm robot name / IP against MIR_HANDOFF.md."
if python mir_command.py Status; then
  echo "SETUP OK"
  exit 0
fi
echo "SETUP INCOMPLETE: Status failed. Check Wi‑Fi reachability, MIR_HOST, and credentials in .env (same as the MiR web UI)."
exit 1
