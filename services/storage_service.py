
import os
from pathlib import PurePosixPath

from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SECRET_KEY = os.getenv("SUPABASE_SECRET_KEY")

BUCKET_NAME = "edusphere-files"


def get_supabase_client():
    """Create and return the Supabase client."""

    if not SUPABASE_URL:
        raise ValueError("SUPABASE_URL is missing from .env")

    if not SUPABASE_SECRET_KEY:
        raise ValueError("SUPABASE_SECRET_KEY is missing from .env")

    return create_client(SUPABASE_URL, SUPABASE_SECRET_KEY)


def validate_storage_path(file_path):
    """Prevent invalid or unsafe storage paths."""

    path = PurePosixPath(file_path)

    if not file_path or path.is_absolute():
        raise ValueError("Invalid storage file path")

    if ".." in path.parts:
        raise ValueError("Invalid storage file path")

    return str(path)


def upload_file(file_bytes, file_path, content_type):
    """Upload file bytes to the private Supabase bucket."""

    if not file_bytes:
        raise ValueError("File is empty")

    safe_path = validate_storage_path(file_path)

    supabase = get_supabase_client()

    result = supabase.storage.from_(BUCKET_NAME).upload(
        path=safe_path,
        file=file_bytes,
        file_options={
            "content-type": content_type,
            "upsert": "false"
        }
    )

    return result


def create_file_url(file_path, expires_in=300):
    """Generate a temporary signed URL for a private file."""

    safe_path = validate_storage_path(file_path)

    supabase = get_supabase_client()

    result = supabase.storage.from_(BUCKET_NAME).create_signed_url(
        safe_path,
        expires_in
    )

    return result["signedURL"]


def download_file(file_path):
    """Download a file from Supabase."""

    safe_path = validate_storage_path(file_path)

    supabase = get_supabase_client()

    return supabase.storage.from_(BUCKET_NAME).download(safe_path)


def delete_file(file_path):
    """Delete a file from Supabase."""

    safe_path = validate_storage_path(file_path)

    supabase = get_supabase_client()

    return supabase.storage.from_(BUCKET_NAME).remove([safe_path])
