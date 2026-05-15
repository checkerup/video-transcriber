#!/usr/bin/env bash
set -euo pipefail

echo "Stopping Video Transcriber..."

# Try systemd first (Linux)
if systemctl --user is-active video-transcriber &>/dev/null; then
    systemctl --user stop video-transcriber
    echo "systemd service stopped."
fi

# Try launchctl (macOS)
if launchctl list | grep -q "com.video-transcriber"; then
    launchctl unload ~/Library/LaunchAgents/com.video-transcriber.plist 2>/dev/null || true
    echo "LaunchAgent stopped."
fi

# Kill any remaining process
pkill -f "video_transcriber.main" 2>/dev/null && echo "Process killed." || echo "No running process found."
