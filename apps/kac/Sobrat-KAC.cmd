@echo off
chcp 65001 >nul
py -3 "%~dp0assemble.py" %*
set "KAC_EXIT=%ERRORLEVEL%"
if "%~1"=="" pause
exit /b %KAC_EXIT%
