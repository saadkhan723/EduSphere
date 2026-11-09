
import logging

from services.storage_service import get_supabase_client, BUCKET_NAME

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

print("Connecting to Supabase...")

try:
    supabase = get_supabase_client()
    print("Supabase client created successfully!")

    print("Checking storage bucket...")

    buckets = supabase.storage.list_buckets()

    bucket_names = [
        bucket.name if hasattr(bucket, "name") else bucket.get("name")
        for bucket in buckets
    ]

    if BUCKET_NAME in bucket_names:
        print(f"SUCCESS: '{BUCKET_NAME}' bucket found!")
    else:
        print("Bucket not found.")
        print("Available buckets:", bucket_names)

except Exception:
    logger.exception("Supabase connection or storage check failed.")
