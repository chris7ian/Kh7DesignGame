#!/usr/bin/env bash
# Build a double-clickable macOS .app bundle for Interste11ar (no installer).
# Requires: Python 3 with pygame and pyinstaller installed.
#
# Usage: ./build_mac_app.sh
# Output: dist/Interste11ar.app

set -e
cd "$(dirname "$0")"

# Ensure we have a venv or system Python with dependencies
if ! python3 -c "import pygame" 2>/dev/null; then
  echo "Installing pygame..."
  pip3 install -r requirements.txt
fi
if ! python3 -c "import PyInstaller" 2>/dev/null; then
  echo "Installing PyInstaller..."
  pip3 install pyinstaller
fi

# Build .app: --windowed = no terminal, creates proper .app on Mac
# --add-data: bundle assets so the game finds them when frozen
# --icon: optional; use your own .icns for the app icon in Finder/Dock
ICON_ARG=""
if [ -f "icon.icns" ]; then
  ICON_ARG="--icon icon.icns"
fi
python3 -m PyInstaller \
  --noconfirm \
  --windowed \
  --name "Interste11ar" \
  $ICON_ARG \
  --add-data "assets:assets" \
  run_game.py

echo ""
echo "Done. Double-click to run: dist/Interste11ar.app"
echo "You can move Interste11ar.app anywhere (e.g. Applications folder)."
