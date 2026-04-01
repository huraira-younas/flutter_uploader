# Installer guide (end-user experience)

Goal: ship a **double-click installer** so users don’t run Python.

## Windows (recommended: Installer EXE)

1. Build the app binaries:

```powershell
.\installer\scripts\build_win.ps1
```

2. Create the installer with **Inno Setup**:

- Install Inno Setup
- Compile `installer/windows/FlutterUploader.iss` (GUI or `ISCC.exe`)

Output goes to `dist-installer/FlutterUploader-Setup.exe`.

**What the installer does**

- Installs to Program Files
- Creates a **Desktop shortcut** (launcher)
- Adds Start Menu entry
- Optionally launches the app on finish

**Uninstall (Windows)**

- **Settings → Apps** (or Control Panel → Programs): uninstall **Flutter Uploader**, or
- Start Menu folder **Flutter Uploader → Uninstall Flutter Uploader**, or
- From the repo (or copy the script next to the user):  
  `.\installer\windows\uninstall.ps1`  
  Add `-Silent` for a quiet uninstall.

The installer also removes `config.json`, `.env`, `secrets\`, `logs\`, and `outputs\` under the install folder when uninstalling.

### Windows code signing (optional but recommended)

- With a code signing cert, you can sign the generated `FlutterUploader-Setup.exe` (and/or `dist\FlutterUploader.exe`) to reduce SmartScreen warnings.
- Inno Setup also supports signing during build via `SignTool` config (left out here since it depends on your certificate + tooling).

## macOS (recommended: DMG)

1. Build the `.app`:

```bash
./installer/scripts/build_mac.sh
```

2. Package as a DMG:

```bash
./installer/mac/build_dmg.sh
```

Output goes to `dist-installer/FlutterUploader.dmg`.

**What the user does**

- Opens the DMG
- Drags `FlutterUploader.app` to **Applications** (shortcut included in the DMG)
- Launches from Applications (or Spotlight)

**Uninstall (macOS)**

- Open the DMG (or keep a copy of **`Uninstall.command`** from the disk image) and double-click **Uninstall.command**, or
- From a terminal: `./installer/mac/uninstall.sh`

These remove `FlutterUploader.app` from `/Applications` and `~/Applications` if present.

### macOS signing + notarization (recommended for distribution)

Unsigned apps may show warnings on other Macs. If you have an Apple Developer account:

```bash
./installer/mac/sign_and_notarize.sh
./installer/mac/build_dmg.sh
```

This signs `dist/FlutterUploader.app`, submits it to Apple notarization, staples the ticket, then you package the DMG.

## Notes (real distribution)

- Unsigned apps may show security warnings.
- For public distribution you’ll want:
  - macOS: codesign + notarization
  - Windows: code signing certificate

