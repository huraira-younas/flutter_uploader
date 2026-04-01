#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

echo "Flutter Uploader installer build (macOS)"
echo
echo "This builds the app and packages a DMG in dist-installer/."
echo

./installer/scripts/build_mac.sh
./installer/mac/build_dmg.sh

echo
echo "Done."
echo "DMG: dist-installer/FlutterUploader.dmg"

