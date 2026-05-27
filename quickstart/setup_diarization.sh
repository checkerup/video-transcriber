#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
echo "======================================================="
echo "  Video Transcriber — Setup Speaker Diarization Extra"
echo "======================================================="
echo ""

if [ ! -d "venv" ]; then
    echo "[INFO] Virtual environment not found. Automatically running standard installation first..."
    chmod +x install.sh
    ./install.sh
fi

if [ ! -d "venv" ]; then
    echo "[ERROR] Virtual environment not found."
    exit 1
fi

source venv/bin/activate
echo "Installing speaker diarization extra (pyannote.audio)..."
pip install -e .[diarization]

echo ""
echo "======================================================="
echo "  Installation Complete!"
echo ""
echo "  NOTE: To use speaker diarization, you must configure:"
echo "  1. Hugging Face account and accept models terms:"
echo "     - https://huggingface.co/pyannote/speaker-diarization-3.1"
echo "     - https://huggingface.co/pyannote/segmentation-3.0"
echo "  2. Set your Hugging Face token in config.yaml under:"
echo "     diarization:"
echo "       enabled: true"
echo "       auth_token: \"your_token_here\""
echo "======================================================="
echo ""
