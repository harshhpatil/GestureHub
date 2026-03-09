#!/bin/bash
# GestureHub Launcher - Always uses the correct Python environment

cd "$(dirname "$0")"

if [ ! -d "venv" ]; then
    echo "ERROR: Virtual environment not found!"
    echo "Run: python3 -m venv venv && venv/bin/pip install -r requirements.txt"
    exit 1
fi

# Always use venv Python
./venv/bin/python main.py
