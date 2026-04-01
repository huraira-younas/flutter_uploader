#!/usr/bin/env bash
set -euo pipefail

# Removes Flutter Uploader from typical install locations (drag-to-Applications DMG).
# Usage:
#   ./installer/mac/uninstall.sh
# Or double-click Uninstall.command from the DMG (created by build_dmg.sh).

APP_BUNDLE="FlutterUploader.app"
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

echo "Done."
