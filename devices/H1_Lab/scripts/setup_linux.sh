#!/usr/bin/env bash
# Idempotent H1_Lab setup for Linux.
# Safe to re-run. Resolves paths from this script's location (zip/USB friendly).
# Not yet verified on Linux hardware — see docs/SETUP.md troubleshooting.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DEVICE_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
PYCONTROL_ROOT="$(cd "${DEVICE_DIR}/../.." && pwd)"
NON_INTERACTIVE=0
MODE="manual"
SET_DEVICE_ID=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --non-interactive) NON_INTERACTIVE=1; shift ;;
    --discover) MODE="discover"; shift ;;
    --device-id) SET_DEVICE_ID="${2:-}"; shift 2 ;;
    -h|--help)
      echo "Usage: $0 [--non-interactive] [--discover | --device-id SERIAL]"
      exit 0
      ;;
    *) echo "Unknown option: $1"; exit 2 ;;
  esac
done

echo "PyControl root: ${PYCONTROL_ROOT}"
echo "Device folder:  ${DEVICE_DIR}"

if [[ ! -f "${DEVICE_DIR}/h1_control.py" ]]; then
  echo "ERROR: h1_control.py not found in ${DEVICE_DIR}"
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

"${PYTHON_BIN}" -c 'import venv' 2>/dev/null || {
  echo "ERROR: python3-venv missing. On Debian/Ubuntu: sudo apt install python3-venv"
  exit 1
}

# USB (FTDI) system library. Installing it needs sudo, so only report here.
if ! ldconfig -p 2>/dev/null | grep -q "libftdi1"; then
  echo "ERROR: libftdi1 not found. On Debian/Ubuntu: sudo apt install libftdi1-2 libusb-1.0-0"
  exit 1
fi

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

if [[ -n "${SET_DEVICE_ID}" ]]; then
  python h1_control.py discover --set-device-id "${SET_DEVICE_ID}"
elif [[ "${MODE}" == "discover" ]]; then
  python h1_control.py discover --save || true
elif [[ "${NON_INTERACTIVE}" -eq 0 ]]; then
  DEFAULT_ID="$(python -c 'import json; print(json.load(open("config.json"))["ftdi_device_id"])')"
  echo ""
  echo "How should we set the H1 USB serial (FTDI device id)?"
  echo "  1) Manual (recommended) — use/edit a serial [default: ${DEFAULT_ID}]"
  echo "  2) Auto-discover — list FTDI USB devices on this computer"
  read -r -p "Choose 1 or 2 [1]: " CHOICE
  CHOICE="${CHOICE:-1}"
  if [[ "${CHOICE}" == "2" ]]; then
    python h1_control.py discover --save || {
      echo "Discovery did not save a serial. Falling back to manual."
      read -r -p "Enter H1 serial [${DEFAULT_ID}]: " TYPED
      TYPED="${TYPED:-$DEFAULT_ID}"
      python h1_control.py discover --set-device-id "${TYPED}"
    }
  else
    read -r -p "Enter H1 serial [${DEFAULT_ID}]: " TYPED
    TYPED="${TYPED:-$DEFAULT_ID}"
    python h1_control.py discover --set-device-id "${TYPED}"
  fi
fi

echo ""
echo "Verifying connection (read-only status; the tray does not move)..."
if python h1_control.py status; then
  echo "SETUP OK"
  exit 0
fi
echo "SETUP INCOMPLETE: status failed. Check H1 power + USB cable, USB permissions (udev rule, see docs/SETUP.md), and ftdi_device_id in config.json."
exit 1
