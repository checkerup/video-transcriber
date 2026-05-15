#!/usr/bin/env bash
set -euo pipefail

if [ ! -d "venv" ]; then
    echo "[ERROR] venv not found. Run ./install.sh first."
    exit 1
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
