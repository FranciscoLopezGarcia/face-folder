@echo off
setlocal EnableExtensions
cd /d "%~dp0"

echo ==============================================
echo   Face Folder - ordenar fotos por persona
echo ==============================================
echo.
echo No necesitas instalar Python ni configurar nada manualmente.
echo La primera vez necesita internet y puede tardar varios minutos.
echo.
echo IMPORTANTE: el modelo buffalo_l es solo para investigacion no comercial.
echo Para trabajo comercial hace falta otra licencia o un modelo compatible.
echo.

set "APP_DIR=%LOCALAPPDATA%\FaceFolder"
if not defined LOCALAPPDATA set "APP_DIR=%USERPROFILE%\FaceFolder"
set "UV_DIR=%APP_DIR%\bin"
set "UV=%UV_DIR%\uv.exe"
set "UV_CACHE_DIR=%APP_DIR%\cache"
set "UV_PYTHON_INSTALL_DIR=%APP_DIR%\python"
set "ORDENAR_FOTOS_MODELOS=%APP_DIR%\modelos"

if not exist "%UV%" (
    echo Preparando Face Folder por primera vez...
    echo Esto descarga el motor de instalacion seguro desde astral.sh.
    if not exist "%UV_DIR%" mkdir "%UV_DIR%"
    set "UV_INSTALL_DIR=%UV_DIR%"
    set "UV_NO_MODIFY_PATH=1"
    powershell -NoProfile -ExecutionPolicy Bypass -Command "try { Invoke-RestMethod 'https://astral.sh/uv/install.ps1' | Invoke-Expression } catch { Write-Error $_; exit 1 }"
    if errorlevel 1 goto :install_error
)

if not exist "%UV%" goto :install_error

echo 1. Arrastra aqui la CARPETA con las fotos y presiona Enter.
set /p "PHOTO_DIR=Carpeta de fotos: "
set "PHOTO_DIR=%PHOTO_DIR:"=%"
if not defined PHOTO_DIR goto :folder_error
if not exist "%PHOTO_DIR%\" goto :folder_error

echo.
echo 2. Opcional: arrastra una carpeta de destino y presiona Enter.
echo    Si presionas Enter sin escribir nada, el resultado queda junto a las fotos.
set /p "DEST_DIR=Carpeta de destino (opcional): "
set "DEST_DIR=%DEST_DIR:"=%"

echo.
echo Analizando. No cierres esta ventana...
echo.
if defined DEST_DIR (
    "%UV%" run --python 3.11 --managed-python --with-requirements "%~dp0requirements.txt" "%~dp0sort_faces.py" "%PHOTO_DIR%" "%DEST_DIR%"
    set "SHOWN_DIR=%DEST_DIR%"
) else (
    "%UV%" run --python 3.11 --managed-python --with-requirements "%~dp0requirements.txt" "%~dp0sort_faces.py" "%PHOTO_DIR%"
    set "SHOWN_DIR=%PHOTO_DIR%"
)
set "RUN_STATUS=%ERRORLEVEL%"

echo.
if not "%RUN_STATUS%"=="0" goto :run_error
echo Terminado. Se abrira la carpeta que contiene el resultado.
start "" explorer.exe "%SHOWN_DIR%"
echo.
pause
exit /b 0

:install_error
echo.
echo ERROR: no se pudo preparar Face Folder.
echo Revisa la conexion a internet y vuelve a abrir Empezar.bat.
echo Si sigue fallando, guarda una captura de toda esta ventana.
pause
exit /b 1

:folder_error
echo.
echo ERROR: no se encontro esa carpeta.
echo Vuelve a abrir Empezar.bat e intenta nuevamente.
pause
exit /b 1

:run_error
echo ERROR: Face Folder no pudo terminar el analisis.
echo Revisa los mensajes anteriores y guarda una captura si necesitas ayuda.
pause
exit /b %RUN_STATUS%
