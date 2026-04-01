# Flutter Uploader — Build & Send

> One pipeline for **Android** and **iOS**: build, sign, copy artifacts, upload to Drive, and optional App Store release—without juggling terminal order.

| Resource | Where |
|:---|:---|
| **Read Me (app)** | Tabs: **README** · **CLI** · **Environment** |
| **CLI** | [`CLI_REFERENCE.md`](CLI_REFERENCE.md) |
| **Secrets & setup** | [`ENVIRONMENT.md`](ENVIRONMENT.md) · `secrets/enviroment.json` |
| **GUI settings** | **Settings** tab: **Environment** (paths, Drive, Gmail, recipients) + **Theme** |

---

## Quick start

1. **Flutter project** — In **Settings → Environment**, set **Flutter project root** (folder that contains `pubspec.yaml`) and click **Save environment**.

2. Run the app from the repo:

```bash
cd /path/to/this/repo
python3 run.py          # GUI — Windows: python run.py
# OR
./run                   # macOS/Linux helper → GUI
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

Artifacts are copied into **`outputs/`** (next to the app); the Flutter project's `build/` trees are left as-is.

---

## Section toggles

Each pipeline section has an **Enabled** switch. Turning a section off skips its steps. If the Flutter project root is missing or invalid, affected sections show a message and stay disabled until you fix **Settings → Environment**.

---

## Settings

### Environment

Values are saved to **`config.json`** and **`secrets/enviroment.json`**, applied for the current run:

| Area | What |
|:---|:---|
| **Project** | Flutter project root |
| **Google Drive** | OAuth client JSON, optional token + parent folder ID |
| **Email** | Gmail address & app password |
| **Logs \| Distribution** | **Logs** — build-report recipients (`LOGS_DISTRIBUTION`). **Distribution** — Drive link emails (`DISTRIBUTION`). Both live in `secrets/enviroment.json`. |

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

## Google Drive

- Uploads **`outputs/`** to a Drive folder (link sharing as configured).
- Link appears in the **Console** tab; optional emails use Gmail + recipient lists from **Settings**.
- Needs OAuth **Desktop** client JSON (Drive API enabled). See [`ENVIRONMENT.md`](ENVIRONMENT.md).

---

## App Store Connect *(Mac)*

- IPA upload via **`xcrun altool`**.
- API key **`.p8`** in `~/private_keys/` plus `APP_STORE_ISSUER_ID` and `APP_STORE_API_KEY` in **Settings → Environment**.

---

## Environment

All environment configuration lives in **`secrets/enviroment.json`** (git-ignored). Edit it via **Settings → Environment → Save environment** or directly. Full variable list: [`ENVIRONMENT.md`](ENVIRONMENT.md).

---

## Prerequisites

| Topic | You need |
|:---|:---|
| **Core** | Python 3.10+ · Flutter · Git on `PATH` |
| **iOS** *(Mac)* | Xcode · CocoaPods · signing + provisioning |
| **Drive** | GCP project · Drive API · OAuth client JSON |
| **App Store** | Connect API key (`.p8`) · Issuer ID · Key ID |

---

## Build reports & logs

Every run (success, fail, or stop):

- **Log file** → `logs/` (timestamped text file).
- **HTML email** (if Gmail is configured): sent only to **`LOGS_DISTRIBUTION`** in `secrets/enviroment.json` (Settings → **Logs**).  
  Email includes status, summary, step table, and attaches the log file.

If Gmail is not set, logs are still written locally.

---

## CLI

[`CLI_REFERENCE.md`](CLI_REFERENCE.md) · **Read Me → CLI** in the app. Use **`--cli`** for headless.
