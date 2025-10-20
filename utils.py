import os
import shutil

from files import DATABASE_FILE, GTFS_FILE, LAST_UPDATED_FILE, EXTRACTED_DIRECTORY

def delete_file(path: str) -> None:
    """
    Delete a file or directory (recursively if directory).
    """
    if os.path.isdir(path):
        shutil.rmtree(path)
        print(f"Deleted directory '{path}'")
    elif os.path.isfile(path):
        os.remove(path)
        print(f"Deleted file '{path}'")
    else:
        print(f"'{path}' does not exist")

def reset(enabled: bool) -> None:
    if not enabled:
        return

    print(f"Resetting Files")
    print(f"Deleting extracted folder, last_updated.txt, gtfs.zip, gtfs.sqlite...")
    delete_file(EXTRACTED_DIRECTORY)
    delete_file(LAST_UPDATED_FILE)
    delete_file(GTFS_FILE)
    delete_file(DATABASE_FILE)
    print("Reset finished")