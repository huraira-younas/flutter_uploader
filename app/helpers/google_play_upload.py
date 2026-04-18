from __future__ import annotations

from googleapiclient.http import MediaFileUpload
from googleapiclient.discovery import build
from google.oauth2 import service_account
from pathlib import Path
import os

from helpers.types import LogFn, StopCheckFn

def run_google_play_upload(
    aab_path: Path,
    packageName: str,
    json_key_path: Path,
    track: str = "production",
    log: LogFn = print,
    stop_check: StopCheckFn | None = None,
) -> bool:
    """Upload an AAB file to Google Play Console using a Service Account."""
    if not aab_path.exists():
        log(f"Error: AAB file not found at {aab_path}\n")
        return False
    
    if not json_key_path.exists():
        log(f"Error: Google Play JSON key not found at {json_key_path}\n")
        return False

    try:
        log(f">> Authenticating with Google Play Service Account...\n")
        scopes = ["https://www.googleapis.com/auth/androidpublisher"]
        creds = service_account.Credentials.from_service_account_file(
            str(json_key_path), scopes=scopes
        )
        service = build("androidpublisher", "v3", credentials=creds)

        log(f">> Creating new edit for package: {packageName}\n")
        edit = service.edits().insert(packageName=packageName, body={}).execute()
        edit_id = edit["id"]

        log(f">> Uploading AAB: {aab_path.name}\n")
        media = MediaFileUpload(
            str(aab_path), mimetype="application/octet-stream", resumable=True
        )
        
        bundle_response = service.edits().bundles().upload(
            editId=edit_id,
            packageName=packageName,
            media_body=media
        ).execute()
        
        version_code = bundle_response["versionCode"]
        log(f"   Success: Uploaded version code {version_code}\n")

        if stop_check and stop_check():
            log("Upload cancelled by user before track assignment.\n")
            return False

        log(f">> Assigning version {version_code} to track: {track}\n")
        track_body = {
            "track": track,
            "releases": [
                {
                    "versionCodes": [str(version_code)],
                    "status": "completed"
                }
            ]
        }
        
        service.edits().tracks().update(
            editId=edit_id,
            track=track,
            packageName=packageName,
            body=track_body
        ).execute()

        log(f">> Committing edit...\n")
        service.edits().commit(editId=edit_id, packageName=packageName).execute()
        
        log(f"OK: Successfully deployed to Google Play ({track} track).\n")
        return True

    except Exception as e:
        log(f"Google Play Upload Failed: {e}\n")
        return False
