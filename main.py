from datetime import datetime

from data_processing import update_gtfs_data
from config import VERSION_FILE
from cloud import upload_file_to_cloud_storage
from database import close_database


def cloud_update_gtfs(request):
    """Cloud Function entry point."""
    try:
        start: datetime = datetime.now()
        was_updated = update_gtfs_data()

        if was_updated:
            # Use the helper function for uploads if needed
            # upload_file_to_cloud_storage(VERSION_FILE)

            total_time = (datetime.now() - start).seconds
            return f'Finished updating data, took {total_time} seconds\n', 200
        else:
            return 'No update needed\n', 200

    except Exception as e:
        print(f"Error: {e}")
        return f'Error: {str(e)}', 500

    finally:
        close_database()

