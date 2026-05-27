#!/usr/bin/env bash
cd "$(dirname "$0")/.."
export PYTHONPATH=src

echo "=============================================="
echo "  Video Transcriber — Convert to MP3"
echo "=============================================="
echo ""

if [ "$#" -eq 0 ]; then
    read -rp "Enter video file path(s) (space-separated): " filepaths
else
    filepaths="$*"
fi

if [ -z "$filepaths" ]; then
    echo "[ERROR] No files specified."
    exit 1
fi

if [ ! -d "venv" ]; then
    echo "[WARN] Virtual environment not found. Automatically running setup..."
    chmod +x install.sh
    ./install.sh
fi

source venv/bin/activate
echo ""
echo "Converting to MP3: $filepaths"
echo ""
python3 -m video_transcriber.main --convert-mp3 $filepaths
