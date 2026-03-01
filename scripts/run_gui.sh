#!/bin/bash
# Run GUI with virtual environment Python

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_PYTHON="$SCRIPT_DIR/.venv/bin/python"

if [ ! -f "$VENV_PYTHON" ]; then
    echo "Virtual environment not found. Please run: python3.12 -m venv .venv"
    exit 1
fi

exec "$VENV_PYTHON" "$SCRIPT_DIR/gui.py" "$@"
