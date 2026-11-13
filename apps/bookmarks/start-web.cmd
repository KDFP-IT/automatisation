@echo off
setlocal
cd /d "%~dp0"
set "BUNDLED_PYTHON=%USERPROFILE%\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
if exist ".venv\Scripts\python.exe" (
  ".venv\Scripts\python.exe" "webapp\launch.py" %*
) else if exist "%BUNDLED_PYTHON%" (
  "%BUNDLED_PYTHON%" "webapp\launch.py" %*
) else (
  python "webapp\launch.py" %*
)
if errorlevel 1 (
  echo.
  echo Could not start the PDF service. See the error above.
  echo Install Python 3.12 if Python is not available.
  pause
)
