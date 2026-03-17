#!/bin/bash
set -euo pipefail

cd "$(dirname "$0")"

if [ ! -d "venv" ]; then
    echo "ERROR: Virtual environment not found!"
    echo "Run: python3 -m venv venv && venv/bin/pip install -r requirements.txt"
    exit 1
fi

LOG_DIR="logs"
mkdir -p "$LOG_DIR"

TS="$(date +%Y%m%d_%H%M%S)"
SERVER_LOG="$LOG_DIR/server_$TS.log"
APP_LOG="$LOG_DIR/app_$TS.log"

echo "Starting command server..."
./venv/bin/python run_server.py > "$SERVER_LOG" 2>&1 &
SERVER_PID=$!
echo "Server PID: $SERVER_PID"
echo "Server log: $SERVER_LOG"

cleanup() {
    echo ""
    echo "Shutting down..."
    if kill -0 "$SERVER_PID" 2>/dev/null; then
        kill "$SERVER_PID" 2>/dev/null || true
        wait "$SERVER_PID" 2>/dev/null || true
    fi
    echo "Stopped server."
}
trap cleanup EXIT INT TERM

sleep 1
if ! kill -0 "$SERVER_PID" 2>/dev/null; then
    echo "ERROR: Server failed to start. Check $SERVER_LOG"
    exit 1
fi

echo "Starting main app..."
echo "App log: $APP_LOG"
./venv/bin/python main.py 2>&1 | tee "$APP_LOG"
