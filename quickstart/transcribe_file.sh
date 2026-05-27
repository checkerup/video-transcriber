#!/usr/bin/env bash
cd "$(dirname "$0")/.."
export PYTHONPATH=src

echo "=============================================="
echo "  Video Transcriber — Transcribe File"
echo "=============================================="
echo ""

filepath="${1:-}"
if [ -z "$filepath" ]; then
    read -rp "Enter the file path (video or audio): " filepath
fi

if [ -z "$filepath" ]; then
    echo "[ERROR] No file path specified."
    exit 1
fi

if [ ! -d "venv" ]; then
    echo "[WARN] Virtual environment not found. Automatically running setup..."
    chmod +x install.sh
    ./install.sh
fi

source venv/bin/activate
echo ""
echo "Processing: $filepath"
echo ""
python3 -m video_transcriber.main --file "$filepath"
