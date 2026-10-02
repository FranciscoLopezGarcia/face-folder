@echo off
setlocal
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" goto :needs_install
".venv\Scripts\python.exe" -c "import sys" >nul 2>&1
if errorlevel 1 goto :needs_install

if not "%~1"=="" (
    ".venv\Scripts\python.exe" sort_faces.py %*
    exit /b %errorlevel%
)

echo ==============================================
echo   Face Folder - ordenar fotos por persona
echo ==============================================
echo.
set /p "PHOTO_DIR=Carpeta de fotos: "
set "PHOTO_DIR=%PHOTO_DIR:"=%"
if not defined PHOTO_DIR (
    echo ERROR: no se indico una carpeta.
    exit /b 1
)

".venv\Scripts\python.exe" sort_faces.py "%PHOTO_DIR%"
exit /b %errorlevel%

:needs_install
echo ERROR: el entorno no esta instalado o esta dañado.
echo Ejecuta primero: install_windows.bat
exit /b 1
