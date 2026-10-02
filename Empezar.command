#!/bin/bash
set -u

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR" || exit 1

clean_path() {
    printf '%s' "$1" | sed \
        -e 's/[[:space:]]*$//' \
        -e 's/^[[:space:]]*//' \
        -e 's/^"\(.*\)"$/\1/' \
        -e "s/^'\(.*\)'$/\1/" \
        -e 's/\\\(.\)/\1/g'
}

echo "=============================================="
echo "  Face Folder - ordenar fotos por persona"
echo "=============================================="
echo
echo "No necesitas instalar Python ni configurar nada manualmente."
echo "La primera vez necesita internet y puede tardar varios minutos."
echo
echo "IMPORTANTE: el modelo buffalo_l es sólo para investigación no comercial."
echo "Para trabajo comercial hace falta otra licencia o un modelo compatible."
echo

APP_DIR="$HOME/Library/Application Support/FaceFolder"
UV_DIR="$APP_DIR/bin"
UV="$UV_DIR/uv"
export UV_CACHE_DIR="$APP_DIR/cache"
export UV_PYTHON_INSTALL_DIR="$APP_DIR/python"
export ORDENAR_FOTOS_MODELOS="$APP_DIR/modelos"

if [ ! -x "$UV" ]; then
    echo "Preparando Face Folder por primera vez..."
    echo "Esto descarga el motor de instalación seguro desde astral.sh."
    mkdir -p "$UV_DIR" || exit 1
    export UV_INSTALL_DIR="$UV_DIR"
    export UV_NO_MODIFY_PATH=1
    if ! curl -LsSf https://astral.sh/uv/install.sh | sh; then
        echo
        echo "ERROR: no se pudo preparar Face Folder."
        echo "Revisa la conexión a internet y vuelve a intentarlo."
        read -r -p "Enter para cerrar" _
        exit 1
    fi
fi

echo "1. Arrastra aquí la CARPETA con las fotos y presiona Enter."
printf "Carpeta de fotos: "
read -r raw_photo_dir
photo_dir=$(clean_path "$raw_photo_dir")

if [ ! -d "$photo_dir" ]; then
    echo
    echo "ERROR: no se encontró esa carpeta."
    read -r -p "Enter para cerrar" _
    exit 1
fi

echo
echo "2. Opcional: arrastra una carpeta de destino y presiona Enter."
echo "   Si presionas Enter sin escribir nada, el resultado queda junto a las fotos."
printf "Carpeta de destino (opcional): "
read -r raw_dest_dir
dest_dir=$(clean_path "$raw_dest_dir")

echo
echo "Analizando. No cierres esta ventana..."
echo
if [ -n "$dest_dir" ]; then
    "$UV" run --python 3.11 --managed-python \
        --with-requirements "$SCRIPT_DIR/requirements.txt" \
        "$SCRIPT_DIR/sort_faces.py" "$photo_dir" "$dest_dir"
    status=$?
    shown_dir="$dest_dir"
else
    "$UV" run --python 3.11 --managed-python \
        --with-requirements "$SCRIPT_DIR/requirements.txt" \
        "$SCRIPT_DIR/sort_faces.py" "$photo_dir"
    status=$?
    shown_dir="$photo_dir"
fi

echo
if [ "$status" -eq 0 ]; then
    echo "Terminado. Se abrirá la carpeta que contiene el resultado."
    open "$shown_dir"
else
    echo "ERROR: Face Folder no pudo terminar el análisis."
    echo "Revisa los mensajes anteriores y guarda una captura si necesitas ayuda."
fi
read -r -p "Enter para cerrar" _
exit "$status"
