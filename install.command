#!/bin/bash
set -u

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR" || exit 1

echo "=============================================="
echo "  Face Folder - instalación para macOS"
echo "=============================================="
echo

PYTHON_BIN=""
for candidate in python3.13 python3.12 python3.11 python3.10 python3; do
    if command -v "$candidate" >/dev/null 2>&1 && \
       "$candidate" -c 'import sys; raise SystemExit(0 if sys.version_info >= (3, 10) else 1)' >/dev/null 2>&1; then
        PYTHON_BIN="$candidate"
        break
    fi
done

if [ -z "$PYTHON_BIN" ]; then
    echo "ERROR: se necesita Python 3.10 o posterior."
    echo "Descárgalo desde https://www.python.org/downloads/macos/"
    exit 1
fi

"$PYTHON_BIN" --version
echo

if [ -x ".venv/bin/python" ] && ! .venv/bin/python -c 'import sys' >/dev/null 2>&1; then
    echo "El entorno existente está incompleto. Se va a reconstruir."
    "$PYTHON_BIN" -m venv --clear .venv || exit 1
elif [ ! -x ".venv/bin/python" ]; then
    echo "Creando el entorno virtual .venv..."
    "$PYTHON_BIN" -m venv .venv || exit 1
fi

echo "Instalando dependencias..."
.venv/bin/python -m pip install --upgrade pip || exit 1
.venv/bin/python -m pip install -r requirements.txt || exit 1

echo
echo "AVISO DE LICENCIA DEL MODELO"
echo "El código de este repositorio es MIT, pero buffalo_l de InsightFace"
echo "está limitado a investigación no comercial. El uso profesional o"
echo "comercial requiere otra licencia o un modelo compatible."
printf "¿Descargar y preparar buffalo_l ahora? [s/N] "
read -r answer
case "$answer" in
    s|S|si|SI|sí|Sí)
        .venv/bin/python sort_faces.py --download-models || exit 1
        ;;
    *)
        echo "Se descargará en la primera ejecución."
        ;;
esac

echo
echo "Instalación completa."
echo "Ejecuta: bash start.command \"/Users/tu_usuario/Fotos/Evento\""
