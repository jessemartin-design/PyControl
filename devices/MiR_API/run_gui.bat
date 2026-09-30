@echo off
REM Start the MiR GUI using this project's .venv.
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  echo Missing .venv\Scripts\python.exe
  echo Finish setup first. See docs\MIR_SETUP.md or scripts\setup_windows.ps1.
  exit /b 1
)
".venv\Scripts\python.exe" -m gui %*
