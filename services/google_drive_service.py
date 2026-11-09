
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload


BASE_DIR = Path(__file__).resolve().parent.parent
TOKEN_FILE = BASE_DIR / "token.json"

SCOPES = ["https://www.googleapis.com/auth/drive.file"]

ROOT_FOLDER_NAME = "EduSphere"

SUBFOLDERS = [
    "Study Materials",
    "Chapters",
    "Assignments",
    "Attendance",
    "Slides",
]


def save_credentials(credentials):
    """Save Google OAuth credentials securely on the server."""
    TOKEN_FILE.write_text(credentials.to_json(), encoding="utf-8")


def get_credentials():
    """Load and refresh saved Google OAuth credentials."""
    if not TOKEN_FILE.exists():
        return None

    credentials = Credentials.from_authorized_user_file(
        str(TOKEN_FILE),
        SCOPES
    )

    if credentials.expired and credentials.refresh_token:
        credentials.refresh(Request())
        save_credentials(credentials)

    if not credentials.valid:
        return None

    return credentials


def get_drive_service():
    """Create Google Drive API service."""
    credentials = get_credentials()

    if credentials is None:
        return None

    return build("drive", "v3", credentials=credentials)


def is_drive_connected():
    """Check whether Google Drive is connected."""
    return get_drive_service() is not None


def find_folder(service, folder_name, parent_id=None):
    """Find an existing folder by name and optional parent folder."""
    escaped_name = folder_name.replace("\\", "\\\\").replace("'", "\\'")

    query = (
        "mimeType = 'application/vnd.google-apps.folder' "
        "and trashed = false "
        f"and name = '{escaped_name}'"
    )

    if parent_id:
        query += f" and '{parent_id}' in parents"

    results = service.files().list(
        q=query,
        spaces="drive",
        fields="files(id, name)",
        pageSize=100
    ).execute()

    folders = results.get("files", [])
    return folders[0] if folders else None


def create_folder(service, folder_name, parent_id=None):
    """Create a Google Drive folder."""
    metadata = {
        "name": folder_name,
        "mimeType": "application/vnd.google-apps.folder"
    }

    if parent_id:
        metadata["parents"] = [parent_id]

    return service.files().create(
        body=metadata,
        fields="id, name"
    ).execute()


def get_or_create_folder(service, folder_name, parent_id=None):
    """Return an existing folder or create it if missing."""
    folder = find_folder(service, folder_name, parent_id)

    if folder:
        print(f"Already exists: {folder_name}")
        return folder

    folder = create_folder(service, folder_name, parent_id)
    print(f"Created: {folder_name}")

    return folder


def create_edusphere_folders():
    """Create EduSphere root folder and its standard subfolders."""
    service = get_drive_service()

    if service is None:
        raise RuntimeError("Google Drive is not connected.")

    root_folder = get_or_create_folder(
        service,
        ROOT_FOLDER_NAME
    )

    created_folders = {}

    for folder_name in SUBFOLDERS:
        folder = get_or_create_folder(
            service,
            folder_name,
            root_folder["id"]
        )

        created_folders[folder_name] = folder["id"]

    return {
        "root": root_folder,
        "subfolders": created_folders
    }


def get_study_materials_folder_id(service):
    """Get or create the EduSphere Study Materials folder."""
    root_folder = get_or_create_folder(
        service,
        ROOT_FOLDER_NAME
    )

    study_folder = get_or_create_folder(
        service,
        "Study Materials",
        root_folder["id"]
    )

    return study_folder["id"]


def get_chapters_folder_id(service):
    """Get or create the EduSphere Chapters folder."""
    root_folder = get_or_create_folder(
        service,
        ROOT_FOLDER_NAME
    )

    chapters_folder = get_or_create_folder(
        service,
        "Chapters",
        root_folder["id"]
    )

    return chapters_folder["id"]


def upload_file_to_drive(uploaded_file, filename, mime_type, folder_id=None):
    """Upload a file to the specified Drive folder."""
    service = get_drive_service()

    if service is None:
        raise RuntimeError("Google Drive is not connected.")

    if not folder_id:
        folder_id = get_study_materials_folder_id(service)

    uploaded_file.stream.seek(0)

    media = MediaIoBaseUpload(
        uploaded_file.stream,
        mimetype=mime_type,
        resumable=True
    )

    metadata = {
        "name": filename,
        "parents": [folder_id]
    }

    result = service.files().create(
        body=metadata,
        media_body=media,
        fields="id, name, mimeType, webViewLink"
    ).execute()

    return result


def delete_drive_file(file_id):
    """Delete a file from Google Drive."""
    service = get_drive_service()

    if service is None:
        raise RuntimeError("Google Drive is not connected.")

    service.files().delete(
        fileId=file_id
    ).execute()

    return True
