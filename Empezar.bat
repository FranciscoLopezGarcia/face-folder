@echo off
setlocal
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" goto :install
".venv\Scripts\python.exe" -c "import sys" >nul 2>&1
if errorlevel 1 goto :install
goto :start

:install
call install_windows.bat
if errorlevel 1 exit /b %errorlevel%

:start
call start_windows.bat %*
exit /b %errorlevel%
