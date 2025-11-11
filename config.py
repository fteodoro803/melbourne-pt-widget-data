import os

class MyFile:
    def __init__(self, name):
        self.name = name
        self.path = os.path.join(TEMP_DIR, name)
    def __str__(self):
        return self.name

# CLOUD
IS_CLOUD = os.getenv('FUNCTION_TARGET') is not None     # Detects if running on Google Cloud or Local
TEMP_DIR = "/tmp" if IS_CLOUD else "."
BUCKET_NAME = "ptv-widget-gtfs-schedule"

# FILES AND DIRECTORIES
GTFS_FILE: MyFile = MyFile("gtfs.zip")
EXTRACTED_DIRECTORY: MyFile = MyFile("extracted")
DATABASE_FILE: MyFile = MyFile("gtfs_database.sqlite")      # todo: delete
VERSION_FILE: MyFile  = MyFile("gtfs_version.txt")

# TESTING
KEEP_TEMP_FILES = False