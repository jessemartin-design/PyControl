#!/usr/bin/env bash
# Idempotent H1_Lab setup for macOS.
# Safe to re-run. Resolves paths from this script's location (zip/USB friendly).
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DEVICE_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
PYCONTROL_ROOT="$(cd "${DEVICE_DIR}/../.." && pwd)"
NON_INTERACTIVE=0
MODE="manual"   # manual | discover
SET_DEVICE_ID=""
INSTALL_DEPS=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --non-interactive) NON_INTERACTIVE=1; shift ;;
    --discover) MODE="discover"; shift ;;
    --device-id) SET_DEVICE_ID="${2:-}"; shift 2 ;;
    --install-deps) INSTALL_DEPS=1; shift ;;
    -h|--help)
      echo "Usage: $0 [--non-interactive] [--discover | --device-id SERIAL] [--install-deps]"
      echo "  --install-deps  allow 'brew install libftdi libusb' without asking"
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

# Prefer python3.12/3.11/3.10/3.9 when available; accept 3.9+
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
  echo "ERROR: Python 3 not found. Install Python 3.9+ from python.org or Homebrew, then re-run."
  exit 1
fi

PY_VERSION="$("${PYTHON_BIN}" -c 'import sys; print("%d.%d" % sys.version_info[:2])')"
"${PYTHON_BIN}" -c 'import sys; raise SystemExit(0 if sys.version_info >= (3, 9) else 1)' || {
  echo "ERROR: Need Python 3.9+. Found ${PY_VERSION} (${PYTHON_BIN})"
  exit 1
}
echo "Using ${PYTHON_BIN} (${PY_VERSION})"

# USB (FTDI) libraries come from Homebrew on macOS.
if ! command -v brew >/dev/null 2>&1; then
  echo "ERROR: Homebrew not found. Install it from https://brew.sh, then re-run."
  exit 1
fi
BREW_PREFIX="$(brew --prefix)"

MISSING_PKGS=()
for pkg in libftdi libusb; do
  brew list --versions "${pkg}" >/dev/null 2>&1 || MISSING_PKGS+=("${pkg}")
done
if [[ ${#MISSING_PKGS[@]} -gt 0 ]]; then
  echo "Missing Homebrew packages: ${MISSING_PKGS[*]}"
  if [[ "${INSTALL_DEPS}" -eq 0 && "${NON_INTERACTIVE}" -eq 0 ]]; then
    read -r -p "Install them now with brew? [y/N]: " ANSWER
    [[ "${ANSWER}" =~ ^[Yy]$ ]] && INSTALL_DEPS=1
  fi
  if [[ "${INSTALL_DEPS}" -eq 1 ]]; then
    brew install "${MISSING_PKGS[@]}"
  else
    echo "ERROR: run 'brew install ${MISSING_PKGS[*]}' (or re-run with --install-deps)."
    exit 1
  fi
fi

cd "${DEVICE_DIR}"

if [[ ! -d .venv ]]; then
  echo "Creating virtual environment (.venv)..."
  "${PYTHON_BIN}" -m venv .venv
else
  echo "Virtual environment already exists — reusing .venv"
fi

# Python finds the Homebrew USB libraries through DYLD_LIBRARY_PATH.
if ! grep -q "DYLD_LIBRARY_PATH" .venv/bin/activate; then
  {
    echo ""
    echo "# H1_Lab: Homebrew FTDI/USB libraries"
    echo "export DYLD_LIBRARY_PATH=\"${BREW_PREFIX}/opt/libftdi/lib:${BREW_PREFIX}/lib\${DYLD_LIBRARY_PATH:+:\$DYLD_LIBRARY_PATH}\""
  } >> .venv/bin/activate
  echo "Added DYLD_LIBRARY_PATH to .venv/bin/activate"
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
echo "SETUP INCOMPLETE: status failed. Check H1 power + USB cable, close any other program using the H1, and check ftdi_device_id in config.json."
exit 1
