import os

from data_processing import update_gtfs_data
from files import DATABASE_FILE, VERSION_FILE, MyFile, IS_CLOUD
from google.cloud import storage

BUCKET_NAME = "ptv-widget-gtfs-schedule"

def cloud_update_gtfs(request):
    """Cloud Function entry point."""
    try:
        was_updated, date_of_data = update_gtfs_data()

        if was_updated:
            # Use the helper function for uploads
            upload_to_cloud_storage(BUCKET_NAME, DATABASE_FILE)
            upload_to_cloud_storage(BUCKET_NAME, VERSION_FILE)

            return 'Data updated successfully!\n', 200
        else:
            return 'No update needed\n', 200

    except Exception as e:
        print(f"Error: {e}")
        return f'Error: {str(e)}', 500

def upload_to_cloud_storage(bucket_name: str, file: MyFile):
    """Helper that works both locally and in cloud, can be used for testing."""

    if not IS_CLOUD:
        print(f"[LOCAL MODE] Would upload {file.name}")
        return

    client = storage.Client()
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(file.name)
    blob.upload_from_filename(file.path)