#!/usr/bin/env bash
set -euo pipefail

if [ ! -d "venv" ]; then
    echo "[ERROR] venv not found. Run ./install.sh first."
    exit 1
fi

source venv/bin/activate

while true; do
    echo ""
    echo "  ╔══════════════════════════════════════════════╗"
    echo "  ║       Video Transcriber — Main Menu          ║"
    echo "  ╚══════════════════════════════════════════════╝"
    echo ""
    echo "  [1]  Start daemon              (watch folder)"
    echo "  [2]  Process single file       (one-shot)"
    echo "  [3]  Screen recording          (manual, Ctrl+C stop)"
    echo "  [4]  Watch process + record    (auto on program launch)"
    echo "  [5]  Check hardware            (CPU/RAM/GPU)"
    echo "  [6]  Re-run setup wizard"
    echo "  [7]  Install autostart"
    echo "  [8]  Uninstall autostart"
    echo "  [9]  Push to GitHub"
    echo "  [0]  Exit"
    echo ""

    read -rp "  Your choice: " choice

    case "$choice" in
        1) python -m video_transcriber.main ;;
        2) read -rp "  Enter video file path: " fp; python -m video_transcriber.main --file "$fp" ;;
        3) echo "  Recording... Ctrl+C to stop"; python -m video_transcriber.main --record ;;
        4) read -rp "  Enter process name (e.g. zoom): " pn; python -m video_transcriber.main --watch-process "$pn" ;;
        5) python -m video_transcriber.main --check-hardware ;;
        6) python -m video_transcriber.main --setup ;;
        7) python -m video_transcriber.main --install-autostart ;;
        8) python -m video_transcriber.main --uninstall-autostart ;;
        9)
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
