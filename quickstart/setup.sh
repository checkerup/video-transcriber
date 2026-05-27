#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
echo "=============================================="
echo "  Video Transcriber — Setup Standard Environment"
echo "=============================================="
echo ""
chmod +x install.sh
./install.sh
echo ""
echo "Setup completed."
