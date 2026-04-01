# Environment

All environment configuration is stored in **`app/secrets/enviroment.json`** (git-ignored).  Edit it directly or use **Settings → Environment → Save environment** in the GUI.

**Flutter project root** — absolute path to the Flutter project this app runs pipelines against (directory that contains `pubspec.yaml`). Set it in **Settings → Environment**; it is stored as **`FLUTTER_PROJECT_ROOT`**.

**Theme** — the selected GUI theme is saved in `config.json` under `app_info.theme`.

**Read Me → Environment** in the GUI · [`README.md`](README.md)

---

## Variables

| Variable | Notes |
|:---|:---|
| `FLUTTER_PROJECT_ROOT` | Path to Flutter project (`pubspec.yaml`) |
| `GOOGLE_DRIVE_CREDENTIALS_JSON` | OAuth Desktop client JSON (path; relative paths are from this app directory) |
| `GOOGLE_DRIVE_TOKEN_JSON` | Optional · default `gdrive_token.json` beside the client secret |
| `GOOGLE_DRIVE_FOLDER_ID` | Optional Drive folder ID |
| `GMAIL_USER` · `GMAIL_APP_PASSWORD` | Optional · Gmail for build reports & Drive link email |
| `LOGS_DISTRIBUTION` · `DISTRIBUTION` | JSON arrays in **`app/secrets/enviroment.json`** · build-report vs Drive-link recipient lists |
| `APP_STORE_ISSUER_ID` · `APP_STORE_API_KEY` | iOS upload (`altool`) |

---

## Google Drive

1. [Google Cloud Console](https://console.cloud.google.com/) — project → enable **Drive API** → **Credentials** → OAuth client **Desktop** → download JSON.
2. Set `GOOGLE_DRIVE_CREDENTIALS_JSON` in Settings → Environment (e.g. `gdrive.json` in the secrets folder).
3. First run opens a browser; token saved (override with `GOOGLE_DRIVE_TOKEN_JSON`).

---

## Gmail *(optional)*

[`App passwords`](https://myaccount.google.com/apppasswords) for `GMAIL_APP_PASSWORD`. Without Gmail, logs stay local only.

---

## App Store *(Mac)*

[App Store Connect](https://appstoreconnect.apple.com/) → **Keys** → `.p8`, Issuer ID, Key ID. Put `.p8` under `~/private_keys/`. Set `APP_STORE_ISSUER_ID` and `APP_STORE_API_KEY` (Key ID) in Settings → Environment.

---

## Tooling

Python 3.10+ · Flutter · Git · *(iOS)* Xcode, CocoaPods
