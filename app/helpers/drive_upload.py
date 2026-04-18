from __future__ import annotations
"""Upload ``outputs/`` to Google Drive (OAuth user credentials)."""

from pathlib import Path

from core.constants import (
    DRIVE_SCOPES,
    UPLOADER_DIR,
    OUTPUTS_DIR,
    FOLDER_MIME,
    LINK_PREFIX,
    MIME_MAP,
)

from core.config_store import distribution_recipients_from_config, env_value
from helpers.types import LogFn, StopCheckFn


def _resolve_env_path(raw: str) -> Path:
    p = Path(raw.strip()).expanduser()
    if p.is_absolute():
        return p
    return (UPLOADER_DIR / p).resolve()


def _drive_email_recipients(recipients: str | None) -> list[str]:
    raw = (recipients or "").strip()
    if raw:
        return [e.strip() for e in raw.split(",") if e.strip() and "@" in e.strip()]
    return distribution_recipients_from_config()


def _email_drive_link(
    link: str,
    recipients: list[str],
    log: LogFn,
    label: str = "Build",
    file_names: list[str] | None = None,
    version: str = "",
    build: str = "",
) -> bool:
    from helpers.build_report import send_drive_link_email
    return send_drive_link_email(
        link=link, label=label,
        file_names=file_names or [],
        recipients=recipients,
        version=version, build=build, log=log,
    )


def _get_user_credentials(creds_path: Path, token_path: Path, log: LogFn):
    from google_auth_oauthlib.flow import InstalledAppFlow
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials

    creds = None
    if token_path.is_file():
        creds = Credentials.from_authorized_user_file(str(token_path), DRIVE_SCOPES)

    if creds and creds.expired and creds.refresh_token:
        log("Refreshing Drive token…\n")
        creds.refresh(Request())
    elif not creds or not creds.valid:
        log("Opening browser for Google Drive authorisation…\n")
        flow = InstalledAppFlow.from_client_secrets_file(str(creds_path), DRIVE_SCOPES)
        creds = flow.run_local_server(port=0)

    new_token = creds.to_json()
    if not token_path.is_file() or token_path.read_text(encoding="utf-8") != new_token:
        token_path.write_text(new_token, encoding="utf-8")
    return creds


def _delete_existing_folders(drive, folder_name: str, parent_id: str | None, log: LogFn) -> None:
    safe_name = folder_name.replace("\\", "\\\\").replace("'", "\\'")
    q = f"name = '{safe_name}' and mimeType = '{FOLDER_MIME}' and trashed = false"
    if parent_id:
        q += f" and '{parent_id}' in parents"
    page_token = None
    while True:
        results = drive.files().list(
            q=q, fields="nextPageToken, files(id, name)",
            spaces="drive", pageToken=page_token,
        ).execute()
        for f in results.get("files", []):
            log(f"  Deleting previous folder: {f['name']} ({f['id']})\n")
            drive.files().delete(fileId=f["id"]).execute()
        page_token = results.get("nextPageToken")
        if not page_token:
            break


def upload_outputs_to_drive(
    recipients: str | None,
    log: LogFn,
    version: str = "",
    build: str = "",
    stop_check: StopCheckFn | None = None,
) -> bool:
    """Upload all files from OUTPUTS_DIR to a single Drive folder."""
    if not OUTPUTS_DIR.exists():
        log("Outputs directory not found. Skipping upload.\n")
        return True

    artifacts = sorted(f for f in OUTPUTS_DIR.iterdir() if f.is_file())
    if not artifacts:
        log("No files found in outputs to upload.\n")
        return True

    creds_path_str = env_value("GOOGLE_DRIVE_CREDENTIALS_JSON")
    creds_path = _resolve_env_path(creds_path_str) if creds_path_str else Path()
    if not creds_path_str or not creds_path.is_file():
        log("Drive: set GOOGLE_DRIVE_CREDENTIALS_JSON. Skipping upload.\n")
        return True

    token_path_str = env_value("GOOGLE_DRIVE_TOKEN_JSON")
    token_path = (
        _resolve_env_path(token_path_str)
        if token_path_str
        else creds_path.with_name("gdrive_token.json")
    )

    try:
        from googleapiclient.http import MediaFileUpload
        from googleapiclient.discovery import build as build_service
    except ImportError:
        log("Drive: install google-auth, google-auth-oauthlib, google-api-python-client. Skipping.\n")
        return True

    try:
        creds = _get_user_credentials(creds_path, token_path, log)
        drive = build_service("drive", "v3", credentials=creds)
    except Exception as e:
        log(f"Drive: failed to authenticate: {e}\n")
        return False

    parent_folder_id = env_value("GOOGLE_DRIVE_FOLDER_ID") or None
    version_tag = f" v{version}+{build}" if version and build else ""
    folder_name = f"ReelStay{version_tag}"

    try:
        _delete_existing_folders(drive, folder_name, parent_folder_id, log)

        log(f"Creating Drive folder '{folder_name}' …\n")
        meta: dict = {"name": folder_name, "mimeType": FOLDER_MIME}
        if parent_folder_id:
            meta["parents"] = [parent_folder_id]
        folder = drive.files().create(body=meta, fields="id").execute()
        folder_id = folder["id"]

        for artifact in artifacts:
            if stop_check and stop_check():
                log("Upload cancelled by user.\n")
                return False
            mime = MIME_MAP.get(artifact.suffix.lower(), "application/octet-stream")
            file_meta: dict = {"name": artifact.name, "parents": [folder_id]}
            media = MediaFileUpload(str(artifact), mimetype=mime, resumable=True)
            try:
                drive.files().create(body=file_meta, media_body=media).execute()
            finally:
                fd = getattr(media, "_fd", None)
                if fd and not fd.closed:
                    fd.close()
            log(f"  Uploaded: {artifact.name}\n")

        drive.permissions().create(
            fileId=folder_id,
            body={"role": "reader", "type": "anyone"},
        ).execute()

        link = f"{LINK_PREFIX}{folder_id}"
        log(f"Public folder link:\n  {link}\n")

        to_addrs = _drive_email_recipients(recipients)
        if to_addrs:
            uploaded_names = [a.name for a in artifacts]
            _email_drive_link(
                link, to_addrs, log, label="Build",
                file_names=uploaded_names, version=version, build=build,
            )

        log("Drive upload complete.\n")
        return True
    except Exception as e:
        log(f"Drive upload failed: {e}\n")
        return False
    finally:
        try:
            drive.close()
        except Exception:
            pass
