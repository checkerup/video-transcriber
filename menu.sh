#!/usr/bin/env bash
set -euo pipefail

export PYTHONPATH=src

if [ ! -d "venv" ]; then
    echo "[INFO] Virtual environment not found. Automatically running installation..."
    chmod +x install.sh
    ./install.sh
fi

source venv/bin/activate

while true; do
    echo ""
    echo "  ╔══════════════════════════════════════════════╗"
    echo "  ║       Video Transcriber — Main Menu          ║"
    echo "  ╚══════════════════════════════════════════════╝"
    echo ""
    echo "  [1]  Start daemon              (watch folder)"
    echo "  [2]  Process single file / audio (one-shot)"
    echo "  [3]  Convert video(s) to MP3   (supports multiple files)"
    echo "  [4]  Screen recording          (manual, Ctrl+C stop)"
    echo "  [5]  Watch process + record    (auto on program launch)"
    echo "  [6]  Check hardware            (CPU/RAM/GPU)"
    echo "  [7]  Re-run setup wizard"
    echo "  [8]  Install autostart"
    echo "  [9]  Uninstall autostart"
    echo "  [10] Run setup/repair environment"
    echo "  [11] Push to GitHub"
    echo "  [0]  Exit"
    echo ""

    read -rp "  Your choice: " choice

    case "$choice" in
        1) python -m video_transcriber.main ;;
        2) read -rp "  Enter file path (video/audio): " fp; python -m video_transcriber.main --file "$fp" ;;
        3) read -rp "  Enter video file path(s) (space-separated): " fps; python -m video_transcriber.main --convert-mp3 $fps ;;
        4) echo "  Recording... Ctrl+C to stop"; python -m video_transcriber.main --record ;;
        5) read -rp "  Enter process name (e.g. zoom): " pn; python -m video_transcriber.main --watch-process "$pn" ;;
        6) python -m video_transcriber.main --check-hardware ;;
        7) python -m video_transcriber.main --setup ;;
        8) python -m video_transcriber.main --install-autostart ;;
        9) python -m video_transcriber.main --uninstall-autostart ;;
        10) ./install.sh ;;
        11)
            if ! gh auth status &>/dev/null; then
                echo "  Not logged in. Starting login..."
                gh auth login
            fi
            read -rp "  Repository name [video-transcriber]: " rn
            rn=${rn:-video-transcriber}
            gh repo create "$rn" --public --source=. --push
            ;;
        0) exit 0 ;;
        *) echo "  Invalid choice." ;;
    esac

    echo ""
    read -rp "  Press Enter to continue..."
done
