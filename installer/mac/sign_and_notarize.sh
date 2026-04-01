#!/usr/bin/env bash
set -euo pipefail

# Codesign + notarize the macOS .app and staple the ticket.
#
# Prereqs:
# - Apple Developer account + Developer ID Application cert installed in Keychain
# - Xcode command line tools
# - An App-Specific password or an App Store Connect API key for notarytool
#
# Usage (from repo root):
#   1) ./installer/scripts/build_mac.sh
#   2) export MAC_CODESIGN_IDENTITY="Developer ID Application: Your Name (TEAMID)"
#   3) export MAC_NOTARY_PROFILE="notarytool-profile-name"
#      (create profile once: xcrun notarytool store-credentials ...)
#   4) ./installer/mac/sign_and_notarize.sh
#   5) ./installer/mac/build_dmg.sh

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "${ROOT_DIR}"

APP_PATH="dist/FlutterUploader.app"
ZIP_PATH="dist/FlutterUploader.app.zip"

if [[ ! -d "${APP_PATH}" ]]; then
  echo "Missing ${APP_PATH}. Run ./installer/scripts/build_mac.sh first." >&2
  exit 1
fi

IDENTITY="${MAC_CODESIGN_IDENTITY:-}"
PROFILE="${MAC_NOTARY_PROFILE:-}"

if [[ -z "${IDENTITY}" ]]; then
  echo "Set MAC_CODESIGN_IDENTITY to your 'Developer ID Application: ...' identity." >&2
  exit 1
fi

if [[ -z "${PROFILE}" ]]; then
  echo "Set MAC_NOTARY_PROFILE to a notarytool credentials profile name." >&2
  exit 1
fi

echo "Codesigning ${APP_PATH}..."
codesign --force --deep --options runtime --sign "${IDENTITY}" "${APP_PATH}"

echo "Creating ZIP for notarization..."
rm -f "${ZIP_PATH}"
ditto -c -k --keepParent "${APP_PATH}" "${ZIP_PATH}"

echo "Submitting to Apple notarization..."
xcrun notarytool submit "${ZIP_PATH}" --keychain-profile "${PROFILE}" --wait

echo "Stapling ticket..."
xcrun stapler staple "${APP_PATH}"

echo "Verifying..."
spctl --assess --type execute --verbose "${APP_PATH}" || true
codesign --verify --deep --strict --verbose=2 "${APP_PATH}"

rm -f "${ZIP_PATH}"

echo "Done: signed + notarized ${APP_PATH}"

