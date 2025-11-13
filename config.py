import os
from datetime import datetime

class MyFile:
    def __init__(self, name):
        self.name = name
        self.path = os.path.join(TEMP_DIR, name)
    def __str__(self):
        return self.name

# DATA PROCESSING
GTFS_URL = "https://opendata.transport.vic.gov.au/dataset/gtfs-schedule"
TRANSPORT_FILTER = "Tram"  # Can be "Metropolitan", "Tram", etc.
KEEP_FILES = ["routes.txt", "trips.txt", "shapes.txt", "agency.txt"]

# CLOUD
IS_CLOUD = os.getenv('FUNCTION_TARGET') is not None     # Detects if running on Google Cloud or Locally
TEMP_DIR = "/tmp" if IS_CLOUD else "."
BUCKET_NAME = "ptv-widget-gtfs-schedule"

# FILES AND DIRECTORIES
GTFS_FILE: MyFile = MyFile("gtfs.zip")
EXTRACTED_DIRECTORY: MyFile = MyFile("extracted")
DATABASE_FILE: MyFile = MyFile("gtfs_database.sqlite")      # todo: delete
VERSION_FILE: MyFile  = MyFile("gtfs_version.txt")

# TESTING (should be all False in deployment)
KEEP_TEMP_FILES = False
IGNORE_VERSION_CHECK = True
MOCK_OLD_DATE = False            # pretends all date is from 1 January 1990
KEEP_OUTDATED_DATA = False       # in MongoDB Database

OLD_DATE = datetime(1990,1,1)
