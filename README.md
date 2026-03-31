# Flutter Uploader — Build & Send

> One pipeline for **Android** and **iOS**: build, sign, copy artifacts, upload to Drive, and optional App Store release—without juggling terminal order.

| Resource | Where |
|:---|:---|
| **Read Me (app)** | Tabs: **README** · **CLI** · **Environment** |
| **CLI file** | [`CLI_REFERENCE.md`](CLI_REFERENCE.md) |
| **Secrets & setup** | [`ENVIRONMENT.md`](ENVIRONMENT.md) · `.env` (repo root) |
| **Theme settings** | **Settings** tab in the GUI |

---

## Quick start

Standalone Python app: **`FLUTTER_PROJECT_ROOT`** in **`.env`** points at the Flutter project you want to build (the pipeline `cd`s there for build/git steps).

```bash
cd /path/to/this/repo
python3 run.py          # GUI — Windows: python run.py
# OR
./uploader # to run GUI on Windows or MAC 
```

`--cli` runs headless. See [`CLI_REFERENCE.md`](CLI_REFERENCE.md). Dependencies install unless `--no-install`.

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

Artifacts are copied into **`outputs/`** here; the Flutter project’s `build/` trees are left as-is.

---

## Section toggles

Each of **Git**, **Android**, **iOS**, and **Post-build** has an **Enabled** switch. Turning a section off skips all of its steps—handy for Android-only or iOS-only runs.

---

## Themes

The **Settings** tab lets you switch between built-in dark themes:

| Theme | Style |
|:---|:---|
| **Catppuccin Mocha** | Warm pastels (default) |
| **Dracula** | Vibrant purple |
| **Tokyo Night** | Cool, muted blue |
| **Gruvbox** | Earthy, retro |
| **Nord** | Arctic frost |
| **One Dark** | Atom-style |
| **Solarized Dark** | Precision palette |

Click **Apply** on any theme card—the app restarts instantly with the new look. Your choice is saved to `.gui_prefs.json` (git-ignored).

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

- Uploads **`outputs/`** to one Drive folder (link sharing as configured).
- Link appears in the **Console** tab; optional email uses Gmail settings in `.env`.
- Needs OAuth **Desktop** client JSON (Drive API enabled). See [`ENVIRONMENT.md`](ENVIRONMENT.md).

---

## App Store Connect *(Mac)*

- IPA upload via **`xcrun altool`**.
- API key **`.p8`** in `~/private_keys/` plus `APP_STORE_ISSUER_ID` and `APP_STORE_API_KEY` in `.env`.

---

## Environment

Copy **`.env.example`** → **`.env`**. Details: [`ENVIRONMENT.md`](ENVIRONMENT.md). Never commit `.env`.

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

- **Log file** → `logs/` under this repo (timestamped, e.g. `build_v1.0.6+65_2026-03-26_15-30-00.log`).
- **HTML email** → first address in `DISTRIBUTION_EMAILS` (needs `GMAIL_USER` + `GMAIL_APP_PASSWORD`): status banner, summary, step table, full log inline + `.log` attachment.

If Gmail is not set, logs are still written locally.

---

## CLI

[`CLI_REFERENCE.md`](CLI_REFERENCE.md) · **Read Me → CLI**. Use **`--cli`** for headless.
