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
KEEP_FILES = ["routes.txt", "trips.txt", "shapes.txt"]

# CLOUD
IS_CLOUD = os.getenv('FUNCTION_TARGET') is not None     # Detects if running on Google Cloud or Locally
TEMP_DIR = "/tmp" if IS_CLOUD else "."
BUCKET_NAME = "ptv-widget-gtfs-schedule"

# FILES AND DIRECTORIES
GTFS_FILE: MyFile = MyFile("gtfs.zip")
EXTRACTED_DIRECTORY: MyFile = MyFile("extracted")
VERSION_FILE: MyFile  = MyFile("gtfs_version.txt")

# MONGO
MONGO_PASSWORD = "1wxN24DvwXKy55yV"     # todo: change password then make it a secret probably
MONGO_URI = f"mongodb+srv://fernandoagustin803_db_user:{MONGO_PASSWORD}@cluster0.kubarsp.mongodb.net/?appName=Cluster0"
MONGO_DATABASE = "live"

# TESTING (should all be False in deployment)
KEEP_TEMP_FILES = False
IGNORE_VERSION_CHECK = False
MOCK_OLD_DATE = False    # pretends all date is from 1 January 1990
KEEP_OUTDATED_DATA = False  # in MongoDB Database
USE_LIVE_MONGODB = False    # Switches to test database

OLD_DATE = datetime(1990,1,1)
MONGO_DATABASE = MONGO_DATABASE if (IS_CLOUD or USE_LIVE_MONGODB) else "test"
