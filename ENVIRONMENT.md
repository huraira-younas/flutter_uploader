# Environment

Copy **`.env.example`** → **`.env`** next to `run.py`. Do not commit `.env`.

**`FLUTTER_PROJECT_ROOT`** — absolute path to the Flutter project this app runs pipelines against (directory that contains `pubspec.yaml`). Logs and `outputs/` stay in this Python app’s folder.

**Read Me → Environment** in the GUI · [`README.md`](README.md)

---

## Variables

| Variable | Notes |
|:---|:---|
| `FLUTTER_PROJECT_ROOT` | **Required** · path to Flutter project (`pubspec.yaml`) |
| `GOOGLE_DRIVE_CREDENTIALS_JSON` | OAuth Desktop client JSON (path; relative paths are from this app directory) |
| `GOOGLE_DRIVE_TOKEN_JSON` | Optional · default `gdrive_token.json` beside the client secret |
| `GOOGLE_DRIVE_FOLDER_ID` | Optional Drive folder ID |
| `GMAIL_USER` · `GMAIL_APP_PASSWORD` · `DISTRIBUTION_EMAILS` | Optional · email |
| `APP_STORE_ISSUER_ID` · `APP_STORE_API_KEY` | iOS upload (`altool`) |

---

## Google Drive

1. [Google Cloud Console](https://console.cloud.google.com/) — project → enable **Drive API** → **Credentials** → OAuth client **Desktop** → download JSON.
2. In `.env`: `GOOGLE_DRIVE_CREDENTIALS_JSON=...` (e.g. `gdrive.json` in this folder).
3. First run opens a browser; token saved (override with `GOOGLE_DRIVE_TOKEN_JSON`).

---

## Gmail *(optional)*

[`App passwords`](https://myaccount.google.com/apppasswords) for `GMAIL_APP_PASSWORD`. Without Gmail, logs stay local only.

---

## App Store *(Mac)*

[App Store Connect](https://appstoreconnect.apple.com/) → **Keys** → `.p8`, Issuer ID, Key ID. Put `.p8` under `~/private_keys/`. In `.env`: `APP_STORE_ISSUER_ID`, `APP_STORE_API_KEY` (Key ID).

---

## Tooling

Python 3.10+ · Flutter · Git · *(iOS)* Xcode, CocoaPods · *(optional)* Shorebird
