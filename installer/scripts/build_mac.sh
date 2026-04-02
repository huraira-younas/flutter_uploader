#!/usr/bin/env bash
set -euo pipefail

# Build Flutter Uploader macOS executables via PyInstaller.
#
# Outputs:
#   dist/FlutterUploader.app   (GUI, onedir bundle - faster startup than one-file)
#   dist/FlutterUploaderCLI    (CLI)
#
# Usage (from repo root):
#   ./installer/scripts/build_mac.sh

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "${ROOT_DIR}"

python3 -m venv .venv
source .venv/bin/activate

python -m pip install --upgrade pip
python -m pip install -r app/requirements.txt -r installer/requirements-dev.txt

rm -rf build dist
rm -rf dist-installer

pyinstaller -y installer/packaging/flutter_uploader.spec

# COLLECT also writes dist/FlutterUploader/; the .app already contains that payload.
rm -rf "${ROOT_DIR}/dist/FlutterUploader"

# Frozen builds resolve UPLOADER_DIR to the folder containing the binary. The GUI
# .app runs from Contents/MacOS; the CLI binary sits in dist/. Copy docs beside both.
DIST_DIR="${ROOT_DIR}/dist"
MACOS_DIR="${DIST_DIR}/FlutterUploader.app/Contents/MacOS"
for pair in \
  "README.md:README.md" \
  "app/ENVIRONMENT.md:ENVIRONMENT.md" \
  "app/CLI_REFERENCE.md:CLI_REFERENCE.md"; do
  src="${ROOT_DIR}/${pair%%:*}"
  base="${pair#*:}"
  if [[ ! -f "${src}" ]]; then
    echo "Missing required file: ${src}" >&2
    exit 1
  fi
  cp "${src}" "${DIST_DIR}/${base}"
  cp "${src}" "${MACOS_DIR}/${base}"
done

echo
echo "Built:"
echo "  dist/FlutterUploader.app"
echo "  dist/FlutterUploaderCLI"
