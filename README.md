<div align="center">
  <img src="app/assets/icon.png" width="128" height="128" alt="Logo">
  <h1>Flutter Uploader</h1>
</div>

> Build, sign, upload, and distribute Flutter apps — one command, both platforms.

---

## Installation

### From source (development)

```bash
git clone https://github.com/huraira-younas/flutter_uploader
cd flutter_uploader
python3 app/run.py          # GUI — Windows: python app\run.py
python3 app/run.py --cli    # headless
```

Dependencies are installed automatically on first launch. Pass `--no-install` to skip.

### Installers (no Python required)

Pre-built installers let end users double-click and go:

| Platform    | Format         | Build command  |
| :---------- | :------------- | :------------- |
| **Windows** | Inno Setup EXE | `install.cmd`  |
| **macOS**   | DMG            | `./install.sh` |

Full packaging guide: [`installer/INSTALLER_GUIDE.md`](installer/INSTALLER_GUIDE.md).

---

## Prerequisites

| Topic           | You need                                                 |
| :-------------- | :------------------------------------------------------- |
| **Core**        | Python 3.10+ · Flutter · Git on `PATH`                   |
| **iOS** _(Mac)_ | Xcode · CocoaPods · signing + provisioning               |
| **Drive**       | GCP project · Drive API · OAuth client JSON              |
| **App Store**   | Connect API key (`.p8`) · Issuer ID · Key ID             |
| **Play Store**  | Service Account JSON key · Android Developer API enabled |

---

## Project layout

```
flutter_uploader/
├── app/                   # application source
│   ├── README.md          # full app documentation
│   ├── CLI_REFERENCE.md   # CLI flags & examples
│   ├── ENVIRONMENT.md     # environment variable reference
│   ├── core/              # pipeline engine, config, constants
│   ├── gui/               # CustomTkinter GUI
│   ├── helpers/            # shell, drive upload, build reports
│   ├── secrets/           # enviroment.json (git-ignored)
│   ├── outputs/           # build artifacts (git-ignored)
│   └── logs/              # run logs (git-ignored)
├── installer/             # packaging scripts & configs
│   ├── INSTALLER_GUIDE.md
│   ├── packaging/         # PyInstaller specs & entry points
│   ├── scripts/           # build_win.ps1, build_mac.sh
│   ├── windows/           # Inno Setup .iss, uninstall script
│   └── mac/               # DMG builder, sign/notarize, uninstall
├── install.cmd            # one-step Windows installer build
├── install.sh             # one-step macOS installer build
└── README.md              # ← you are here
```

---

## Documentation

| Doc                                                            | Description                                             |
| :------------------------------------------------------------- | :------------------------------------------------------ |
| [`app/README.md`](app/README.md)                               | App usage: pipeline, settings, themes, Drive, App Store |
| [`app/CLI_REFERENCE.md`](app/CLI_REFERENCE.md)                 | CLI flags, section toggles, step selection              |
| [`app/ENVIRONMENT.md`](app/ENVIRONMENT.md)                     | Environment variables & secrets setup                   |
| [`installer/INSTALLER_GUIDE.md`](installer/INSTALLER_GUIDE.md) | Building Windows EXE / macOS DMG installers             |
