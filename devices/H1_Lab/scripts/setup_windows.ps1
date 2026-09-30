# Idempotent H1_Lab setup for Windows (PowerShell 5+ / PowerShell 7).
# Safe to re-run. Resolves paths from this script's location (zip/USB friendly).
# Not yet verified on Windows hardware — see docs/H1_SETUP.md troubleshooting (USB driver).
[CmdletBinding()]
param(
    [switch]$NonInteractive,
    [switch]$Discover,
    [string]$DeviceId = ""
)

$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$DeviceDir = Resolve-Path (Join-Path $ScriptDir "..")
$PyControlRoot = Resolve-Path (Join-Path $DeviceDir "../..")

Write-Host "PyControl root: $PyControlRoot"
Write-Host "Device folder:  $DeviceDir"

if (-not (Test-Path (Join-Path $DeviceDir "h1_control.py"))) {
    throw "h1_control.py not found in $DeviceDir"
}

function Get-PythonCommand {
    foreach ($name in @("python", "py")) {
        $cmd = Get-Command $name -ErrorAction SilentlyContinue
        if ($cmd) { return $cmd.Source }
    }
    return $null
}

$PythonBin = Get-PythonCommand
if (-not $PythonBin) {
    throw "Python not found. Install Python 3.9+ from https://www.python.org/downloads/ and enable 'Add python.exe to PATH'."
}

$versionText = & $PythonBin -c "import sys; print('%d.%d' % sys.version_info[:2])"
& $PythonBin -c "import sys; raise SystemExit(0 if sys.version_info >= (3, 9) else 1)"
if ($LASTEXITCODE -ne 0) {
    throw "Need Python 3.9+. Found $versionText"
}
Write-Host "Using $PythonBin ($versionText)"

Set-Location $DeviceDir

if (-not (Test-Path ".venv")) {
    Write-Host "Creating virtual environment (.venv)..."
    & $PythonBin -m venv .venv
} else {
    Write-Host "Virtual environment already exists — reusing .venv"
}

$Activate = Join-Path $DeviceDir ".venv\Scripts\Activate.ps1"
. $Activate

python -m pip install --upgrade pip | Out-Null
pip install -r requirements.txt

if (-not (Test-Path "config.json")) {
    Copy-Item "config.example.json" "config.json"
    Write-Host "Created config.json from config.example.json"
}

if ($DeviceId) {
    python h1_control.py discover --set-device-id $DeviceId
} elseif ($Discover) {
    python h1_control.py discover --save
} elseif (-not $NonInteractive) {
    $defaultId = python -c "import json; print(json.load(open('config.json'))['ftdi_device_id'])"
    Write-Host ""
    Write-Host "How should we set the H1 USB serial (FTDI device id)?"
    Write-Host "  1) Manual (recommended) — use/edit a serial [default: $defaultId]"
    Write-Host "  2) Auto-discover — list FTDI USB devices on this computer"
    $choice = Read-Host "Choose 1 or 2 [1]"
    if ([string]::IsNullOrWhiteSpace($choice)) { $choice = "1" }
    if ($choice -eq "2") {
        python h1_control.py discover --save
        if ($LASTEXITCODE -ne 0) {
            Write-Host "Discovery did not save a serial. Falling back to manual."
            $typed = Read-Host "Enter H1 serial [$defaultId]"
            if ([string]::IsNullOrWhiteSpace($typed)) { $typed = $defaultId }
            python h1_control.py discover --set-device-id $typed
        }
    } else {
        $typed = Read-Host "Enter H1 serial [$defaultId]"
        if ([string]::IsNullOrWhiteSpace($typed)) { $typed = $defaultId }
        python h1_control.py discover --set-device-id $typed
    }
}

Write-Host ""
Write-Host "Verifying connection (read-only status; the tray does not move)..."
python h1_control.py status
if ($LASTEXITCODE -eq 0) {
    Write-Host "SETUP OK"
    exit 0
}

Write-Host "SETUP INCOMPLETE: status failed. Check H1 power + USB cable, the USB driver (see docs/H1_SETUP.md), and ftdi_device_id in config.json."
exit 1
