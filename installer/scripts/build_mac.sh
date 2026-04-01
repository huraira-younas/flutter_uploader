#!/usr/bin/env bash
set -euo pipefail

# Build Flutter Uploader macOS executables via PyInstaller.
#
# Outputs:
#   dist/FlutterUploader.app   (GUI)
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

echo
echo "Built:"
echo "  dist/FlutterUploader.app"
echo "  dist/FlutterUploaderCLI"
