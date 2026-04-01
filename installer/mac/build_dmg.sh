#!/usr/bin/env bash
set -euo pipefail

# Builds a user-friendly DMG with a drag-to-Applications flow.
#
# Usage (from repo root, on macOS):
#   1) ./installer/scripts/build_mac.sh
#   2) ./installer/mac/build_dmg.sh
#
# Output:
#   dist-installer/FlutterUploader.dmg

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "${ROOT_DIR}"

APP_PATH="dist/FlutterUploader.app"
DMG_DIR="dist-installer"
DMG_PATH="${DMG_DIR}/FlutterUploader.dmg"
STAGING_DIR="${DMG_DIR}/_dmg_staging"
VOL_NAME="Flutter Uploader"

mkdir -p "${DMG_DIR}"
rm -f "${DMG_PATH}"

if [[ ! -d "${APP_PATH}" ]]; then
  echo "Missing ${APP_PATH}. Run ./installer/scripts/build_mac.sh first." >&2
  exit 1
fi

# Always clean staging dir, even on errors.
cleanup() {
  rm -rf "${STAGING_DIR}"
}
trap cleanup EXIT

# DMG staging folder with Applications shortcut.
rm -rf "${STAGING_DIR}"
mkdir -p "${STAGING_DIR}"
cp -R "${APP_PATH}" "${STAGING_DIR}/"
ln -s /Applications "${STAGING_DIR}/Applications"

# Simple DMG creation (unsigned). For distribution outside your machine, you'll want codesign+notarize.
TMP_DMG="${DMG_DIR}/_tmp_flutter_uploader.dmg"
rm -f "${TMP_DMG}"

echo "Creating DMG..."
hdiutil create -volname "${VOL_NAME}" -srcfolder "${STAGING_DIR}" -ov -format UDZO "${TMP_DMG}"
mv "${TMP_DMG}" "${DMG_PATH}"

echo "Built ${DMG_PATH}"

