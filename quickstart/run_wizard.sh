#!/usr/bin/env bash
cd "$(dirname "$0")/.."
export PYTHONPATH=src

echo "=============================================="
echo "  Video Transcriber — Setup Wizard"
echo "=============================================="
echo ""

if [ ! -d "venv" ]; then
    echo "[WARN] Virtual environment not found. Automatically running setup..."
    chmod +x install.sh
    ./install.sh
fi

source venv/bin/activate
python3 -m video_transcriber.main --setup
echo ""
