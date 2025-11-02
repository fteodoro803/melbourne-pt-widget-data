from data_processing import update_gtfs_data
from config import DATABASE_FILE, VERSION_FILE
from cloud import upload_file_to_cloud_storage


def cloud_update_gtfs(request):
    """Cloud Function entry point."""
    try:
        was_updated, date_of_data = update_gtfs_data()

        if was_updated:
            # Use the helper function for uploads
            upload_file_to_cloud_storage(DATABASE_FILE)
            upload_file_to_cloud_storage(VERSION_FILE)

            return 'Data updated successfully!\n', 200
        else:
            return 'No update needed\n', 200

    except Exception as e:
        print(f"Error: {e}")
        return f'Error: {str(e)}', 500

