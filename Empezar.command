#!/bin/bash
set -u

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR" || exit 1

if [ ! -x ".venv/bin/python" ] || ! .venv/bin/python -c 'import sys' >/dev/null 2>&1; then
    bash install.command || exit 1
fi

exec bash start.command "$@"
