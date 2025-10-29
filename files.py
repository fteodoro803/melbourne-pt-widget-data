import os

# DETECT IF RUNNING IN GOOGLE CLOUD OR LOCAL
IS_CLOUD = os.getenv('FUNCTION_TARGET') is not None  # Google Cloud sets this
TEMP_DIR = "/tmp" if IS_CLOUD else "."

gtfs = "gtfs.zip"
extracted = "extracted"
database = "gtfs.sqlite"
version = "version.txt"

# FILES AND DIRECTORIES
GTFS_FILE: str = os.path.join(TEMP_DIR, gtfs)
EXTRACTED_DIRECTORY: str = os.path.join(TEMP_DIR, extracted)
DATABASE_FILE: str = os.path.join(TEMP_DIR, database)
LAST_UPDATED_FILE: str = os.path.join(TEMP_DIR, version)
