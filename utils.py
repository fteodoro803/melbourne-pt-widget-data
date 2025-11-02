import os
import shutil

from config import DATABASE_FILE, GTFS_FILE, VERSION_FILE, EXTRACTED_DIRECTORY, MyFile


def delete_file(file: MyFile) -> None:
    """
    Delete a file or directory (recursively if directory).
    """
    path = file.path

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
    print(f"Deleting {EXTRACTED_DIRECTORY.name, VERSION_FILE.name, GTFS_FILE.name, DATABASE_FILE.name}, ...")
    delete_file(EXTRACTED_DIRECTORY)
    delete_file(VERSION_FILE)
    delete_file(GTFS_FILE)
    delete_file(DATABASE_FILE)
    print("Reset finished")