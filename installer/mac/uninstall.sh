#!/usr/bin/env bash
set -euo pipefail

# Removes Flutter Uploader from typical install locations and cleans up
# macOS Library residue (caches, preferences, application support).
#
# Usage:
#   ./installer/mac/uninstall.sh
# Or double-click Uninstall.command from the DMG.

APP_BUNDLE="FlutterUploader.app"
APP_NAME="Flutter Uploader"
BUNDLE_ID="com.senpai.flutteruploader"

LOCATIONS=(
    "/Applications/${APP_BUNDLE}"
    "${HOME}/Applications/${APP_BUNDLE}"
)

Removed=0
for install_path in "${LOCATIONS[@]}"; do
    if [[ -d "${install_path}" ]]; then
        echo "Removing: ${install_path}"
        rm -rf "${install_path}"
        Removed=1
    fi
done

if [[ "${Removed}" -eq 0 ]]; then
    echo "Nothing to remove (${APP_BUNDLE} not found in /Applications or ~/Applications)."
fi

LIBRARY_DIRS=(
    "${HOME}/Library/Application Support/${APP_NAME}"
    "${HOME}/Library/Caches/${BUNDLE_ID}"
)

for lib_path in "${LIBRARY_DIRS[@]}"; do
    if [[ -d "${lib_path}" ]]; then
        echo "Removing: ${lib_path}"
        rm -rf "${lib_path}"
    fi
done

PLIST="${HOME}/Library/Preferences/${BUNDLE_ID}.plist"
if [[ -f "${PLIST}" ]]; then
    echo "Removing: ${PLIST}"
    rm -f "${PLIST}"
fi

echo "Done."
