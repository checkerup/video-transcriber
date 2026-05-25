#!/usr/bin/env bash
set -euo pipefail

echo "============================================"
echo "  Video Transcriber — Installation"
echo "============================================"
echo

# --- Python ---
if ! command -v python3 &>/dev/null; then
    echo "[ERROR] Python 3 not found. Install from https://python.org"
    exit 1
fi
python3 --version
echo

# --- FFmpeg ---
if ! command -v ffmpeg &>/dev/null; then
    echo "[WARN] FFmpeg not found. Attempting to install..."
    if [[ "$(uname)" == "Darwin" ]]; then
        if command -v brew &>/dev/null; then
            brew install ffmpeg
        else
            echo "[ERROR] Install Homebrew first: https://brew.sh"
            exit 1
        fi
    elif [[ "$(uname)" == "Linux" ]]; then
        if command -v apt-get &>/dev/null; then
            sudo apt-get update && sudo apt-get install -y ffmpeg
        elif command -v dnf &>/dev/null; then
            sudo dnf install -y ffmpeg
        elif command -v pacman &>/dev/null; then
            sudo pacman -S --noconfirm ffmpeg
        else
            echo "[ERROR] Install FFmpeg manually: https://ffmpeg.org/download.html"
            exit 1
        fi
    fi
fi
echo "FFmpeg: $(command -v ffmpeg)"
echo

# --- Virtual environment ---
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

echo "Activating venv..."
source venv/bin/activate

# --- Install dependencies ---
echo "Installing Python dependencies..."
pip install --upgrade pip

# Detect Nvidia GPU
if command -v nvidia-smi &>/dev/null; then
    echo "[INFO] NVIDIA GPU detected via nvidia-smi. Installing dependencies with CUDA support..."
    pip install -e .[cuda]
else
    echo "[INFO] No NVIDIA GPU detected. Installing standard dependencies..."
    pip install -e .
fi

# --- Config ---
if [ ! -f "config.yaml" ]; then
    echo "Creating config.yaml from example..."
    cp config.example.yaml config.yaml
    echo
    echo "[IMPORTANT] Edit config.yaml and set:"
    echo "  - watch.folder           = folder to monitor"
    echo "  - processing.output_folder = where to save results"
    echo "  - telegram.bot_token      = your bot token from @BotFather"
    echo "  - telegram.chat_id        = your chat ID"
    echo
fi

if [ ! -f ".env" ]; then
    echo "Creating .env from example..."
    cp .env.example .env
fi

echo
echo "============================================"
echo "  Setup complete!"
echo "  Run: ./start.sh"
echo "============================================"
