@echo off
setlocal
cd /d "%~dp0"

echo ==============================================
echo   Face Folder - instalacion para Windows
echo ==============================================
echo.

set "PYTHON_CMD="
where py >nul 2>&1
if not errorlevel 1 (
    py -3 -c "import sys; raise SystemExit(0 if sys.version_info ^>= (3, 10) else 1)" >nul 2>&1
    if not errorlevel 1 set "PYTHON_CMD=py -3"
)

if not defined PYTHON_CMD (
    where python >nul 2>&1
    if not errorlevel 1 (
        python -c "import sys; raise SystemExit(0 if sys.version_info ^>= (3, 10) else 1)" >nul 2>&1
        if not errorlevel 1 set "PYTHON_CMD=python"
    )
)

if not defined PYTHON_CMD (
    echo ERROR: se necesita Python 3.10 o posterior de 64 bits.
    echo Descargalo desde https://www.python.org/downloads/ y marca
    echo "Add Python to PATH" durante la instalacion.
    exit /b 1
)

echo Python detectado:
%PYTHON_CMD% --version
echo.

if exist ".venv\Scripts\python.exe" (
    ".venv\Scripts\python.exe" -c "import sys" >nul 2>&1
    if errorlevel 1 (
        echo El entorno existente esta incompleto. Se va a reconstruir.
        %PYTHON_CMD% -m venv --clear .venv
    )
) else (
    echo Creando el entorno virtual .venv...
    %PYTHON_CMD% -m venv .venv
)
if errorlevel 1 goto :venv_error

echo Instalando dependencias...
".venv\Scripts\python.exe" -m pip install --upgrade pip
if errorlevel 1 goto :dependency_error
".venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 goto :dependency_error

echo.
echo AVISO DE LICENCIA DEL MODELO
echo El codigo de este repositorio es MIT, pero buffalo_l de InsightFace
echo esta limitado a investigacion no comercial. El uso profesional o
echo comercial requiere otra licencia o un modelo compatible.
choice /C SN /N /M "Descargar y preparar buffalo_l ahora? [S/N] "
if errorlevel 2 goto :model_skipped

".venv\Scripts\python.exe" sort_faces.py --download-models
if errorlevel 1 goto :model_error

echo.
echo Instalacion completa.
echo Ejecuta: start_windows.bat "C:\Fotos\Evento"
exit /b 0

:model_skipped
echo.
echo Dependencias instaladas. El modelo se descargara en la primera ejecucion.
echo Ejecuta: start_windows.bat "C:\Fotos\Evento"
exit /b 0

:venv_error
echo ERROR: no se pudo crear .venv. Revisa permisos y espacio disponible.
exit /b 1

:dependency_error
echo ERROR: no se pudieron instalar las dependencias. Revisa internet y el mensaje anterior.
exit /b 1

:model_error
echo ERROR: no se pudo preparar el modelo. Revisa internet y el mensaje anterior.
exit /b 1
