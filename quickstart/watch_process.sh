#!/usr/bin/env bash
cd "$(dirname "$0")/.."
export PYTHONPATH=src

echo "=============================================="
echo "  Video Transcriber — Watch Process"
echo "=============================================="
echo ""

procname="${1:-}"
if [ -z "$procname" ]; then
    read -rp "Enter the process name to watch (e.g. zoom): " procname
fi

if [ -z "$procname" ]; then
    echo "[ERROR] No process name specified."
    exit 1
fi

if [ ! -d "venv" ]; then
    echo "[WARN] Virtual environment not found. Automatically running setup..."
    chmod +x install.sh
    ./install.sh
fi

source venv/bin/activate
echo ""
echo "Watching for process: $procname"
echo "Press Ctrl+C to stop watching."
echo ""
python3 -m video_transcriber.main --watch-process "$procname"
