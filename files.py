import os

# DETECT IF RUNNING IN GOOGLE CLOUD OR LOCAL
IS_CLOUD = os.getenv('FUNCTION_TARGET') is not None  # Google Cloud sets this
TEMP_DIR = "/tmp" if IS_CLOUD else "."

# FILES AND DIRECTORIES
class MyFile:
    def __init__(self, name):
        self.name = name
        self.path = os.path.join(TEMP_DIR, name)
    def __str__(self):
        return self.name

GTFS_FILE: MyFile = MyFile("gtfs.zip")
EXTRACTED_DIRECTORY: MyFile = MyFile("extracted")
DATABASE_FILE: MyFile = MyFile("gtfs_database.sqlite")
VERSION_FILE: MyFile  = MyFile("gtfs_version.txt")