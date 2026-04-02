#!/usr/bin/env bash
set -euo pipefail

# Removes Flutter Uploader from typical install locations and cleans up
# macOS Library residue (caches, preferences, application support).
#
# Usage:
#   ./installer/mac/uninstall.sh
# Or double-click Uninstall.command from the DMG.

BUNDLE_ID="com.senpai.flutteruploader"
APP_BUNDLE="FlutterUploader.app"
APP_NAME="Flutter Uploader"

LOCATIONS=(
    "/Applications/${APP_BUNDLE}"
    "${HOME}/Applications/${APP_BUNDLE}"
    "/Applications/${APP_NAME}.app"
    "${HOME}/Applications/${APP_NAME}.app"
)

Removed=0

remove_bundle_if_present() {
    local install_path="$1"
    if [[ ! -d "${install_path}" ]]; then
        return 0
    fi
    echo "Removing: ${install_path}"
    rm -rf "${install_path}"
    Removed=1
}

# Any install path (including renamed copies) as long as Spotlight has indexed it.
while IFS= read -r found_path; do
    [[ -z "${found_path}" ]] && continue
    remove_bundle_if_present "${found_path}"
done < <(mdfind "kMDItemCFBundleIdentifier == '${BUNDLE_ID}'" 2>/dev/null || true)

for install_path in "${LOCATIONS[@]}"; do
    remove_bundle_if_present "${install_path}"
done

if [[ "${Removed}" -eq 0 ]]; then
    for base in /Applications "${HOME}/Applications"; do
        [[ -d "${base}" ]] || continue
        while IFS= read -r -d '' app_path; do
            bid="$(/usr/libexec/PlistBuddy -c 'Print :CFBundleIdentifier' "${app_path}/Contents/Info.plist" 2>/dev/null || true)"
            if [[ "${bid}" == "${BUNDLE_ID}" ]]; then
                remove_bundle_if_present "${app_path}"
            fi
        done < <(find "${base}" -maxdepth 1 -name '*.app' -print0 2>/dev/null)
    done
fi

if [[ "${Removed}" -eq 0 ]]; then
    echo "Nothing to remove (${APP_BUNDLE} not found; try dragging the app to Trash if it was renamed or moved)."
else
    echo "If an icon still appears in Applications, relaunch Finder: Option+right-click Finder → Relaunch."
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
