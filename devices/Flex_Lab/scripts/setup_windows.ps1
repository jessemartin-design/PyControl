# Idempotent Flex_Lab setup for Windows (PowerShell 5+ / PowerShell 7).
# Safe to re-run. Resolves paths from this script's location (zip/USB friendly).
[CmdletBinding()]
param(
    [switch]$NonInteractive,
    [switch]$Discover,
    [string]$Ip = ""
)

$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$DeviceDir = Resolve-Path (Join-Path $ScriptDir "..")
$PyControlRoot = Resolve-Path (Join-Path $DeviceDir "../..")

Write-Host "PyControl root: $PyControlRoot"
Write-Host "Device folder:  $DeviceDir"

if (-not (Test-Path (Join-Path $DeviceDir "flex_control.py"))) {
    throw "flex_control.py not found in $DeviceDir"
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
$ok = & $PythonBin -c "import sys; raise SystemExit(0 if sys.version_info >= (3, 9) else 1)"
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

if ($Ip) {
    python flex_control.py discover --set-ip $Ip
} elseif ($Discover) {
    python flex_control.py discover --save
} elseif (-not $NonInteractive) {
    $defaultIp = python -c "import json; print(json.load(open('config.json'))['robot_ip'])"
    Write-Host ""
    Write-Host "How should we set the Flex IP?"
    Write-Host "  1) Manual (recommended) — use/edit an IP [default: $defaultIp]"
    Write-Host "  2) Auto-discover on this Wi-Fi subnet"
    $choice = Read-Host "Choose 1 or 2 [1]"
    if ([string]::IsNullOrWhiteSpace($choice)) { $choice = "1" }
    if ($choice -eq "2") {
        python flex_control.py discover --save
        if ($LASTEXITCODE -ne 0) {
            Write-Host "Discovery did not save an IP. Falling back to manual."
            $typed = Read-Host "Enter Flex IP [$defaultIp]"
            if ([string]::IsNullOrWhiteSpace($typed)) { $typed = $defaultIp }
            python flex_control.py discover --set-ip $typed
        }
    } else {
        $typed = Read-Host "Enter Flex IP [$defaultIp]"
        if ([string]::IsNullOrWhiteSpace($typed)) { $typed = $defaultIp }
        python flex_control.py discover --set-ip $typed
    }
}

Write-Host ""
Write-Host "Verifying connection (success = event ping_ok)..."
python flex_control.py ping
if ($LASTEXITCODE -eq 0) {
    Write-Host "SETUP OK"
    exit 0
}

Write-Host "SETUP INCOMPLETE: ping failed. Join the robot Wi-Fi and check config.json robot_ip."
exit 1
