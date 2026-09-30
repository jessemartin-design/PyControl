# Idempotent MiR_API setup for Windows (PowerShell 5+ / PowerShell 7).
# Safe to re-run. Resolves paths from this script's location (zip/USB friendly).
[CmdletBinding()]
param(
    [switch]$NonInteractive,
    [string]$Ip = "",
    [string]$HostName = ""
)

$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$DeviceDir = Resolve-Path (Join-Path $ScriptDir "..")
$PyControlRoot = Resolve-Path (Join-Path $DeviceDir "../..")

Write-Host "PyControl root: $PyControlRoot"
Write-Host "Device folder:  $DeviceDir"

if (-not (Test-Path (Join-Path $DeviceDir "mir_command.py"))) {
    throw "mir_command.py not found in $DeviceDir"
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
    throw "Python not found. Install Python 3.10+ from https://www.python.org/downloads/ and enable 'Add python.exe to PATH'."
}

$versionText = & $PythonBin -c "import sys; print('%d.%d' % sys.version_info[:2])"
& $PythonBin -c "import sys; raise SystemExit(0 if sys.version_info >= (3, 10) else 1)"
if ($LASTEXITCODE -ne 0) {
    throw "Need Python 3.10+. Found $versionText"
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

if (-not (Test-Path ".env")) {
    Copy-Item ".env.example" ".env"
    Write-Host "Created .env from .env.example — edit MIR_USERNAME / MIR_PASSWORD (and MIR_HOST if needed)."
}

function Set-MirHost([string]$HostValue) {
    $lines = Get-Content ".env"
    $done = $false
    $out = foreach ($line in $lines) {
        if ($line -match '^MIR_HOST=') {
            "MIR_HOST=$HostValue"
            $done = $true
        } else {
            $line
        }
    }
    if (-not $done) { $out += "MIR_HOST=$HostValue" }
    $out | Set-Content ".env"
    Write-Host "Set MIR_HOST=$HostValue in .env"
}

$TargetHost = if ($Ip) { $Ip } elseif ($HostName) { $HostName } else { "" }

if ($TargetHost) {
    Set-MirHost $TargetHost
} elseif (-not $NonInteractive) {
    $defaultHost = ""
    foreach ($line in Get-Content ".env") {
        if ($line -match '^MIR_HOST=(.*)$') { $defaultHost = $Matches[1]; break }
    }
    Write-Host ""
    Write-Host "Robot IP / host (see MIR_HANDOFF.md for the lab default)."
    if ($defaultHost) {
        $typed = Read-Host "Enter MIR_HOST [$defaultHost]"
        if ([string]::IsNullOrWhiteSpace($typed)) { $typed = $defaultHost }
    } else {
        $typed = Read-Host "Enter MIR_HOST"
    }
    if (-not [string]::IsNullOrWhiteSpace($typed)) {
        Set-MirHost $typed
    }
}

Write-Host ""
Write-Host "Verifying connection (read-only Status; the robot does not move)..."
Write-Host "Confirm robot name / IP against MIR_HANDOFF.md."
python mir_command.py Status
if ($LASTEXITCODE -eq 0) {
    Write-Host "SETUP OK"
    exit 0
}

Write-Host "SETUP INCOMPLETE: Status failed. Check Wi-Fi reachability, MIR_HOST, and credentials in .env (same as the MiR web UI)."
exit 1
