import os
import shutil


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
    delete_file("extracted")
    delete_file("last_updated.txt")
    delete_file("gtfs.zip")
    delete_file("gtfs.sqlite")
    print("Reset finished")