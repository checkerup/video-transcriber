#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
export PYTHONPATH=src

echo "=============================================="
echo "  Video Transcriber — Start Daemon"
echo "=============================================="
echo ""

if [ ! -d "venv" ]; then
    echo "[WARN] Virtual environment not found. Automatically running setup..."
    chmod +x install.sh
    ./install.sh
fi

source venv/bin/activate
echo "Starting daemon (watching folders and processes)..."
echo "Press Ctrl+C to stop."
echo ""
python3 -m video_transcriber.main
