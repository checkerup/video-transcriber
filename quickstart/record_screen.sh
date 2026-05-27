#!/usr/bin/env bash
cd "$(dirname "$0")/.."
export PYTHONPATH=src

echo "=============================================="
echo "  Video Transcriber — Record Screen"
echo "=============================================="
echo ""

if [ ! -d "venv" ]; then
    echo "[WARN] Virtual environment not found. Automatically running setup..."
    chmod +x install.sh
    ./install.sh
fi

source venv/bin/activate
echo "Starting manual screen recording..."
echo "Press Ctrl+C to stop recording."
echo ""
python3 -m video_transcriber.main --record
