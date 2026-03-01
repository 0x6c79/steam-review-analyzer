# -*- mode: python -*-
import sys
import os
import subprocess

# Add virtual environment path
venv_python = os.path.join(os.path.dirname(__file__), ".venv", "bin", "python")
gui_script = os.path.join(os.path.dirname(__file__), "gui.py")

# Check if virtual environment exists
if not os.path.exists(venv_python):
    print("Error: Virtual environment not found!")
    print("Please run: python3.12 -m venv .venv && .venv/bin/pip install -r requirements.txt")
    sys.exit(1)

# Run GUI with virtual environment Python
os.execv(venv_python, [venv_python, gui_script] + sys.argv[1:])
