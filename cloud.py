import os

from main import update_gtfs_data
from files import DATABASE_FILE
from google.cloud import storage

BUCKET_NAME = "ptv-widget-gtfs-schedule"

def cloud_update_gtfs(request):
    """Cloud Function entry point."""
    try:
        was_updated = update_gtfs_data()

        if was_updated:
            # Use the helper function for uploads
            upload_to_cloud_storage(DATABASE_FILE, BUCKET_NAME, 'gtfs.sqlite')

            return 'Data updated successfully!', 200
        else:
            return 'No update needed', 200

    except Exception as e:
        print(f"Error: {e}")
        return f'Error: {str(e)}', 500

def upload_to_cloud_storage(local_file, bucket_name, blob_name):
    """Helper that works both locally and in cloud, can be used for testing."""

    if not os.getenv('FUNCTION_TARGET'):
        print(f"[LOCAL MODE] Would upload {local_file}")
        return

    client = storage.Client()
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(blob_name)
    blob.upload_from_filename(local_file)