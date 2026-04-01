#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"

echo "Flutter Uploader - macOS Installer Build"
echo

echo "Step 1: Building app binaries..."
echo
./installer/scripts/build_mac.sh

echo
echo "Step 2: Packaging DMG..."
echo
./installer/mac/build_dmg.sh

if [[ -d .venv ]]; then
    echo
    echo "Cleaning up build venv..."
    rm -rf .venv
fi

echo
echo "Done! DMG: dist-installer/FlutterUploader.dmg"
