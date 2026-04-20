<div align="center">
  <img src="app/assets/icon.png" width="160" height="160" alt="Flutter Uploader Logo">
  <h1>Flutter Uploader</h1>
  <p align="center">
    <strong>One command. Two platforms. Zero friction.</strong>
    <br />
    The ultimate automated pipeline for building, signing, and distributing Flutter applications.
  </p>

  <p align="center">
    <img src="https://img.shields.io/badge/version-5.6.1-blue.svg" alt="Version 5.6.1">
    <img src="https://img.shields.io/badge/platform-Windows%20%7C%20macOS-lightgrey.svg" alt="Platform">
    <img src="https://img.shields.io/badge/built%20with-Python-blue" alt="Built with Python">
    <img src="https://img.shields.io/badge/License-MIT-green.svg" alt="License MIT">
  </p>
</div>

---

## 🚀 Overview

**Flutter Uploader** is a powerful CI/CD-inspired desktop utility designed to handle the heavy lifting of Flutter application distribution. Whether you're targeting the **Android Play Store**, **Apple App Store**, or manual distribution via **Google Drive**, this tool orchestrates the entire workflow from code cleanup to final release.

Available as a **Modern GUI** (built with CustomTkinter) or a **Headless CLI**, it ensures your release process is consistent, repeatable, and fast.

## ✨ Key Features

- 🏗️ **Unified Pipeline**: Manage Clean, Pub Get, Build, and Sign steps for both platforms in one place.
- 🍏 **iOS Excellence**: Automatic `pod install`, Archive, and IPA export (requires macOS).
- 🤖 **Android Power**: Build release APKs and App Bundles (AAB) with ease.
- ☁️ **Cloud Sync**: Direct integration with Google Drive for instant artifact sharing.
- 🏪 **Store Ready**: Direct upload to **TestFlight** (iOS) and **Play Store Tracks** (Android).
- 🎨 **Beautiful UI**: Modern, responsive interface with **7+ premium themes** (Dracula, Nord, Tokyo Night, etc.).
- 🤖 **Automation**: Fully integrated GitHub Actions workflow for building native installers.
- 📧 **Build Reports**: Automatic HTML build reports sent via Gmail upon completion.
- 🔒 **Secure**: All secrets and keys are stored locally and git-ignored.

---

## 🛠️ Tech Stack

- **Core Logic**: Python 3.10+
- **GUI Framework**: [CustomTkinter](https://github.com/TomSchimansky/CustomTkinter)
- **Packaging**: [PyInstaller](https://www.pyinstaller.org/)
- **Installer Engines**: [Inno Setup](https://jrsoftware.org/isinfo.php) (Windows) & `hdiutil` (macOS DMG)
- **APIs**: Google Drive V3, Android Publisher V3, App Store Connect (`xcrun altool`)

---

## 🚦 Getting Started

### 1. Installation (Development)

Clone the repository and run the application source:

```bash
# Clone the repository
git clone https://github.com/huraira-younas/flutter_uploader

# Navigate to the project root
cd flutter_uploader

# Run the GUI
python app/run.py

# Run the CLI (Headless mode)
python app/run.py --cli
```

> **Note**: Dependencies are handled automatically on the first launch.

### 2. Native Installers (Ready to Use)

For a professional experience, use the pre-built installers:

| Platform    | Installer Type      | Command to Build |
| :---------- | :------------------ | :--------------- |
| **Windows** | `.exe` (Inno Setup) | `install.cmd`    |
| **macOS**   | `.dmg` (Disk Image) | `./install.sh`   |

---

## 📋 Prerequisites

| Category         | Requirement                                     |
| :--------------- | :---------------------------------------------- |
| **Core**         | Python 3.10+, Flutter SDK, Git                  |
| **iOS / macOS**  | Xcode, CocoaPods, Apple Developer Account       |
| **Google Drive** | GCP Project with Drive API enabled + OAuth JSON |
| **App Store**    | App Store Connect API Key (`.p8`)               |
| **Play Store**   | Google Play Service Account JSON Key            |

---

## 📂 Project Architecture

```bash
flutter_uploader/
├── app/                   # Core application source
│   ├── core/              # Pipeline engine & logic
│   ├── gui/               # CustomTkinter interface
│   ├── assets/            # App icons & branding
│   └── secrets/           # environment.json (Private)
├── .github/               # Automated CI/CD Workflows
├── installer/             # Packaging scripts & configs
├── dist-installer/        # Final built installers (Windows/Mac)
├── install.cmd            # One-click Windows Build helper
└── install.sh             # One-click macOS Build helper
```

---

## 📖 Extended Documentation

- 📝 **[App Usage Guide](app/README.md)**: Deep dive into settings, themes, and Drive setup.
- ⌨️ **[CLI Reference](app/CLI_REFERENCE.md)**: Full list of flags for headless automation.
- 🔐 **[Secrets & Environment](app/ENVIRONMENT.md)**: How to configure your API keys.
- 📦 **[Packaging Guide](installer/INSTALLER_GUIDE.md)**: Detailed instructions for building native binaries.

---

<div align="center">
  <p>Made with ❤️ by <b>Senpai</b></p>
</div>
