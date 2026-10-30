@echo off
setlocal
cd /d "%~dp0"
set PYTHONUTF8=1
if not exist ".venv\Scripts\pythonw.exe" (
  echo Bitte zuerst INSTALLIEREN.bat ausfuehren.
  pause
  exit /b 1
)
start "" ".venv\Scripts\pythonw.exe" "Interface\starten.py"
