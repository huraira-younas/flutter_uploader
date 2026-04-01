# Flutter Uploader — Build & Send

> One pipeline for **Android** and **iOS**: build, sign, copy artifacts, upload to Drive, and optional App Store release—without juggling terminal order.

| Resource | Where |
|:---|:---|
| **Read Me (app)** | Tabs: **README** · **CLI** · **Environment** |
| **CLI** | [`app/CLI_REFERENCE.md`](app/CLI_REFERENCE.md) |
| **Secrets & setup** | [`app/ENVIRONMENT.md`](app/ENVIRONMENT.md) · optional `app/.env` |
| **GUI settings** | **Settings** tab: **Environment** (paths, Drive, Gmail, recipients) + **Theme** |

---

## Quick start

1. **Flutter project** — In **Settings → Environment**, set **Flutter project root** (folder that contains `pubspec.yaml`) and click **Save environment**.  
   Optional: set **`FLUTTER_PROJECT_ROOT`** in `app/.env` to override for that run.

2. Run the app from the repo:

```bash
cd /path/to/this/repo
python3 run.py          # GUI — Windows: python run.py
# OR
./run                   # macOS/Linux helper → GUI
```

`--cli` runs headless. See [`app/CLI_REFERENCE.md`](app/CLI_REFERENCE.md). Dependencies install unless `--no-install`.

---

## Platform support

| OS | Android | iOS |
|:---|:---:|:---:|
| **macOS** | ✓ | ✓ |
| **Windows** | ✓ | — |

---

## Pipeline (what runs)

| Phase | Steps |
|:---|:---|
| **Common** | Flutter Clean · Dependencies (`pub get` / `pub upgrade`) |
| **Git (pre)** | Pre-release commit · Pull `master` |
| **Android** | Build APK (release, split-per-abi) |
| **iOS** *(Mac)* | Pod install · Build IPA · App Store upload (`xcrun altool`) |
| **Git (post)** | Release commit · Push `master` |
| **Post-build** | Open `outputs/` · Drive upload + email · Shutdown / sleep |

Artifacts are copied into **`app/outputs/`** (next to the app); the Flutter project’s `build/` trees are left as-is.

---

## Section toggles

Each pipeline section has an **Enabled** switch. Turning a section off skips its steps. If the Flutter project root is missing or invalid, affected sections show a message and stay disabled until you fix **Settings → Environment**.

---

## Settings

### Environment

Configure without editing `.env` (values are saved to **`app/config.json`** and applied for the current run):

| Area | What |
|:---|:---|
| **Project** | Flutter project root |
| **Google Drive** | OAuth client JSON, optional token + parent folder ID |
| **Email** | Gmail address & app password |
| **Logs \| Distribution** | **Logs** — build-report recipients (`LOGS_DISTRIBUTION`). **Distribution** — Drive link emails (`DISTRIBUTION`). Both live in `app/secrets/enviroment.json`. |

### Theme

**Settings → Theme** — pick a preset and **Apply** (app restarts). Saved under `app_info.theme` in `config.json`.

| Theme | Style |
|:---|:---|
| **Catppuccin Mocha** | Warm pastels (default) |
| **Dracula** | Vibrant purple |
| **Tokyo Night** | Cool, muted blue |
| **Gruvbox** | Earthy, retro |
| **Nord** | Arctic frost |
| **One Dark** | Atom-style |
| **Solarized Dark** | Precision palette |

---

## Shorebird

When the Shorebird CLI is on `PATH`, each platform header gets a **Shorebird** toggle and **Release** / **Patch** mode.

| Platform | Default |
|:---|:---|
| **Android** | Off (plain Flutter build) |
| **iOS** | On when CLI is installed |

If Shorebird is missing, the control shows *(not installed)* and stays disabled.

---

## Google Drive

- Uploads **`outputs/`** to a Drive folder (link sharing as configured).
- Link appears in the **Console** tab; optional emails use Gmail + recipient lists from **Settings** or `.env`.
- Needs OAuth **Desktop** client JSON (Drive API enabled). See [`ENVIRONMENT.md`](app/ENVIRONMENT.md).

---

## App Store Connect *(Mac)*

- IPA upload via **`xcrun altool`**.
- API key **`.p8`** in `~/private_keys/` plus `APP_STORE_ISSUER_ID` and `APP_STORE_API_KEY` in `.env`.

---

## Environment file

Copy **`app/.env.example`** → **`app/.env`** if you want file-based overrides. Full variable list: [`app/ENVIRONMENT.md`](app/ENVIRONMENT.md). Never commit `.env`.

---

## Prerequisites

| Topic | You need |
|:---|:---|
| **Core** | Python 3.10+ · Flutter · Git on `PATH` |
| **iOS** *(Mac)* | Xcode · CocoaPods · signing + provisioning |
| **Drive** | GCP project · Drive API · OAuth client JSON |
| **App Store** | Connect API key (`.p8`) · Issuer ID · Key ID |
| **Optional** | Shorebird CLI |

---

## Build reports & logs

Every run (success, fail, or stop):

- **Log file** → `app/logs/` (timestamped text file).
- **HTML email** (if Gmail is configured): sent only to **`LOGS_DISTRIBUTION`** in `app/secrets/enviroment.json` (Settings → **Logs**).  
  Email includes status, summary, step table, and attaches the log file.

If Gmail is not set, logs are still written locally.

---

## Installers (shipping without Python)

See [`installer/INSTALLER_GUIDE.md`](installer/INSTALLER_GUIDE.md): Windows (Inno Setup) and macOS (DMG). Uninstall notes are in that guide.

---

## CLI

[`CLI_REFERENCE.md`](app/CLI_REFERENCE.md) · **Read Me → CLI** in the app. Use **`--cli`** for headless.
