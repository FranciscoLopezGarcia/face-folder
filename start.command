#!/bin/bash
set -u

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR" || exit 1

if [ ! -x ".venv/bin/python" ] || ! .venv/bin/python -c 'import sys' >/dev/null 2>&1; then
    echo "ERROR: el entorno no está instalado o está dañado."
    echo "Ejecuta primero: bash install.command"
    exit 1
fi

if [ "$#" -gt 0 ]; then
    exec .venv/bin/python sort_faces.py "$@"
fi

echo "=============================================="
echo "  Face Folder - ordenar fotos por persona"
echo "=============================================="
echo
printf "Carpeta de fotos: "
read -r photo_dir

if [ -z "$photo_dir" ]; then
    echo "ERROR: no se indicó una carpeta."
    exit 1
fi

exec .venv/bin/python sort_faces.py "$photo_dir"
