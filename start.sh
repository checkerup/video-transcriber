#!/usr/bin/env bash
set -euo pipefail

export PYTHONPATH=src

if [ ! -d "venv" ]; then
    echo "[INFO] Virtual environment not found. Automatically running installation..."
    chmod +x install.sh
    ./install.sh
else
    source venv/bin/activate
    if ! python3 -c "import yaml, watchdog, requests" &>/dev/null; then
        echo "[WARN] Missing required Python packages. Automatically running repair/installation..."
        chmod +x install.sh
        ./install.sh
    fi
fi

source venv/bin/activate

if [ -n "${1:-}" ]; then
    echo "Processing single file: $1"
    python -m video_transcriber.main --file "$1"
else
    echo "Starting Video Transcriber daemon..."
    echo "Watching folder defined in config.yaml"
    echo "Press Ctrl+C to stop"
    echo
    python -m video_transcriber.main
fi
