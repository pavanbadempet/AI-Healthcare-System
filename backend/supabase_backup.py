import logging
import os

import requests

logger = logging.getLogger(__name__)

SUPABASE_URL = os.environ.get("SUPABASE_URL", None)
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", None)
SUPABASE_BUCKET = os.environ.get("SUPABASE_BUCKET", None)

def get_supabase_headers():
    return {
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "apikey": SUPABASE_KEY
    }

def restore_database():
    """Download healthcare.db from Supabase Storage on startup."""
    if not (SUPABASE_URL and SUPABASE_KEY and SUPABASE_BUCKET):
        logger.info("Supabase credentials not fully configured. Skipping DB restore fallback.")
        return False

    db_path = "healthcare.db"
    # Detect Hugging Face Space persistent storage fallback if present
    if os.path.exists("/data") and os.access("/data", os.W_OK):
        db_path = "/data/healthcare.db"

    # Clean URL format
    base_url = SUPABASE_URL.strip().rstrip("/")
    bucket = SUPABASE_BUCKET.strip()
    url = f"{base_url}/storage/v1/object/authenticated/{bucket}/healthcare.db"

    try:
        logger.info("Checking Supabase Storage for database backup...")
        response = requests.get(url, headers=get_supabase_headers(), stream=True, timeout=10.0)

        if response.status_code == 200:
            # Overwrite or create file
            with open(db_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            logger.info("Successfully restored database from Supabase Storage: %s", db_path)
            return True
        elif response.status_code == 404:
            logger.info("No database backup found in Supabase Storage. Starting fresh.")
        else:
            logger.warning("Supabase storage responded with status %d: %s", response.status_code, response.text)
    except Exception as e:
        logger.warning("Failed to restore database from Supabase Storage: %s", e)
    return False

def backup_database():
    """Upload healthcare.db to Supabase Storage."""
    if not (SUPABASE_URL and SUPABASE_KEY and SUPABASE_BUCKET):
        logger.info("Supabase credentials not fully configured. Skipping DB backup.")
        return False

    db_path = "healthcare.db"
    if os.path.exists("/data/healthcare.db"):
        db_path = "/data/healthcare.db"

    if not os.path.exists(db_path):
        logger.warning("Database file not found for backup: %s", db_path)
        return False

    base_url = SUPABASE_URL.strip().rstrip("/")
    bucket = SUPABASE_BUCKET.strip()
    url = f"{base_url}/storage/v1/object/{bucket}/healthcare.db"

    try:
        logger.info("Uploading database backup to Supabase Storage...")
        # Check size to prevent uploading empty files
        if os.path.getsize(db_path) == 0:
            logger.warning("Database file is empty. Skipping upload.")
            return False

        with open(db_path, "rb") as f:
            file_data = f.read()

        # Try to upload using PUT (which overwrites if x-upsert is true)
        headers = get_supabase_headers()
        headers["Content-Type"] = "application/octet-stream"
        headers["x-upsert"] = "true" # Overwrite existing file

        response = requests.put(url, data=file_data, headers=headers, timeout=15.0)
        if response.status_code in (200, 201):
            logger.info("Successfully backed up database to Supabase Storage!")
            return True
        else:
            # Fallback to POST if PUT is not allowed
            response = requests.post(url, data=file_data, headers=headers, timeout=15.0)
            if response.status_code in (200, 201):
                logger.info("Successfully backed up database to Supabase Storage (POST)!")
                return True
            else:
                logger.warning("Supabase backup upload failed (status %d): %s", response.status_code, response.text)
    except Exception as e:
        logger.warning("Failed to back up database to Supabase Storage: %s", e)
    return False
