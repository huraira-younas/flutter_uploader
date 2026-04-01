# Installer Guide

Ship Flutter Uploader as a **double-click installer** so end users never touch Python.

---

## Windows (Installer EXE)

### 1. Build the app binaries

```powershell
.\installer\scripts\build_win.ps1
```

This creates a venv, installs dependencies, and runs PyInstaller. Output:

```
dist\FlutterUploader.exe      (GUI)
dist\FlutterUploaderCLI.exe   (CLI)
```

### 2. Create the installer with Inno Setup

- Install [Inno Setup 6](https://jrsoftware.org/isinfo.php)
- Compile `installer/windows/FlutterUploader.iss` (GUI or command line):

```powershell
& "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" installer\windows\FlutterUploader.iss
```

Output: `dist-installer\FlutterUploader-Setup.exe`

### What the installer does

- Installs to **Program Files**
- Creates a **Desktop shortcut** (optional, checked by default)
- Adds **Start Menu** entries: app launcher, CLI shortcut, and uninstaller
- Optionally launches the app on finish

### Uninstall (Windows)

Three options:

1. **Settings > Apps** (or Control Panel > Programs): uninstall **Flutter Uploader**
2. **Start Menu > Flutter Uploader > Uninstall Flutter Uploader**
3. Standalone script:

```powershell
.\installer\windows\uninstall.ps1
.\installer\windows\uninstall.ps1 -Silent    # quiet mode
```

The installer also removes `config.json`, `secrets\`, `logs\`, and `outputs\` under the install folder during uninstall.

### Windows code signing (optional)

With a code-signing certificate you can sign `FlutterUploader-Setup.exe` (and/or `dist\FlutterUploader.exe`) to suppress SmartScreen warnings. Inno Setup supports signing during build via `SignTool` config (depends on your certificate tooling).

---

## macOS (DMG)

### 1. Build the .app

```bash
./installer/scripts/build_mac.sh
```

Output:

```
dist/FlutterUploader.app    (GUI)
dist/FlutterUploaderCLI     (CLI)
```

### 2. Package as a DMG

```bash
./installer/mac/build_dmg.sh
```

Output: `dist-installer/FlutterUploader.dmg`

### What the user does

1. Open the DMG
2. Drag **FlutterUploader.app** to the **Applications** shortcut in the DMG
3. Launch from **Applications** (or Spotlight)

### Uninstall (macOS)

Two options:

1. Open the DMG and double-click **Uninstall.command**
2. From a terminal:

```bash
./installer/mac/uninstall.sh
```

These remove `FlutterUploader.app` from `/Applications` and `~/Applications`.

### macOS signing + notarization (recommended for distribution)

Unsigned apps trigger Gatekeeper warnings on other Macs. With an Apple Developer account:

```bash
./installer/scripts/build_mac.sh
export MAC_CODESIGN_IDENTITY="Developer ID Application: Your Name (TEAMID)"
export MAC_NOTARY_PROFILE="notarytool-profile-name"
./installer/mac/sign_and_notarize.sh
./installer/mac/build_dmg.sh
```

This codesigns the `.app`, submits it to Apple notarization, staples the ticket, then packages the DMG.

---

## Configuration after install

The installed app stores its configuration in the same directory as the executable:

| File | Purpose |
|:---|:---|
| `config.json` | Section toggles, version, theme, commit messages |
| `secrets/enviroment.json` | Flutter project root, Drive/Gmail credentials, recipient lists |
| `logs/` | Build log files |
| `outputs/` | Copied build artifacts (APK/IPA) |

Use **Settings > Environment** in the GUI to configure paths and credentials. No `.env` files are used.

---

## Notes

- For public distribution you will want code signing on both platforms.
- The CLI executable (`FlutterUploaderCLI`) accepts the same `--cli` flags documented in `CLI_REFERENCE.md`.
- Build artifacts go to `dist/` (PyInstaller) and `dist-installer/` (final installer/DMG). Both are git-ignored.
