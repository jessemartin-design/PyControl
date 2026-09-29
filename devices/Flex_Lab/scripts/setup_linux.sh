#!/usr/bin/env bash
# Idempotent Flex_Lab setup for Linux.
# Safe to re-run. Resolves paths from this script's location (zip/USB friendly).
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DEVICE_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
PYCONTROL_ROOT="$(cd "${DEVICE_DIR}/../.." && pwd)"
NON_INTERACTIVE=0
MODE="manual"
SET_IP=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --non-interactive) NON_INTERACTIVE=1; shift ;;
    --discover) MODE="discover"; shift ;;
    --ip) SET_IP="${2:-}"; shift 2 ;;
    -h|--help)
      echo "Usage: $0 [--non-interactive] [--discover | --ip A.B.C.D]"
      exit 0
      ;;
    *) echo "Unknown option: $1"; exit 2 ;;
  esac
done

echo "PyControl root: ${PYCONTROL_ROOT}"
echo "Device folder:  ${DEVICE_DIR}"

if [[ ! -f "${DEVICE_DIR}/flex_control.py" ]]; then
  echo "ERROR: flex_control.py not found in ${DEVICE_DIR}"
  exit 1
fi

pick_python() {
  for candidate in python3.12 python3.11 python3.10 python3.9 python3; do
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
"${PYTHON_BIN}" -c 'import sys; raise SystemExit(0 if sys.version_info >= (3, 9) else 1)' || {
  echo "ERROR: Need Python 3.9+. Found ${PY_VERSION} (${PYTHON_BIN})"
  exit 1
}
echo "Using ${PYTHON_BIN} (${PY_VERSION})"

# Ensure venv module exists (common Linux gap)
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

if [[ ! -f config.json ]]; then
  cp config.example.json config.json
  echo "Created config.json from config.example.json"
fi

if [[ -n "${SET_IP}" ]]; then
  python flex_control.py discover --set-ip "${SET_IP}"
elif [[ "${MODE}" == "discover" ]]; then
  python flex_control.py discover --save || true
elif [[ "${NON_INTERACTIVE}" -eq 0 ]]; then
  DEFAULT_IP="$(python -c 'import json; print(json.load(open("config.json"))["robot_ip"])')"
  echo ""
  echo "How should we set the Flex IP?"
  echo "  1) Manual (recommended) — use/edit an IP [default: ${DEFAULT_IP}]"
  echo "  2) Auto-discover on this Wi-Fi subnet"
  read -r -p "Choose 1 or 2 [1]: " CHOICE
  CHOICE="${CHOICE:-1}"
  if [[ "${CHOICE}" == "2" ]]; then
    python flex_control.py discover --save || {
      echo "Discovery did not save an IP. Falling back to manual."
      read -r -p "Enter Flex IP [${DEFAULT_IP}]: " TYPED
      TYPED="${TYPED:-$DEFAULT_IP}"
      python flex_control.py discover --set-ip "${TYPED}"
    }
  else
    read -r -p "Enter Flex IP [${DEFAULT_IP}]: " TYPED
    TYPED="${TYPED:-$DEFAULT_IP}"
    python flex_control.py discover --set-ip "${TYPED}"
  fi
fi

echo ""
echo "Verifying connection (success = event ping_ok)..."
if python flex_control.py ping; then
  echo "SETUP OK"
  exit 0
fi
echo "SETUP INCOMPLETE: ping failed. Join the robot Wi-Fi and check config.json robot_ip."
exit 1
