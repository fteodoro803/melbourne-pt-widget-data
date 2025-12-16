import os
import shutil
import re

from config import MyFile, KEEP_TEMP_FILES, TRANSPORTS
from pathlib import Path

def delete_file(file: MyFile) -> None:
    """
    Delete a file or directory (recursively if directory).
    """
    if KEEP_TEMP_FILES:
        print(f"[TEST] Skipping deletion of temporary file {file}")
        return

    path = file.path

    if os.path.isdir(path):
        shutil.rmtree(path)
        print(f"Deleted directory '{path}'")
    elif os.path.isfile(path):
        os.remove(path)
        print(f"Deleted file '{path}'")
    else:
        print(f"'{path}' does not exist")


def get_types_from_path(file_path: str, transports: dict[str, str]) -> tuple[str, str]:
    """
    Extracts the GTFS file type (e.g., trips, routes, shapes)
    and the transport type (mapped from number in the filename).

    Raises:
        ValueError: if either type cannot be determined.
    """

    # 1. Determine GTFS file type from path
    file_type = Path(file_path).stem

    # 2. Extract transport number from path
    match = re.search(r'\d+', file_path)
    transport_num = match.group() if match else None

    # 3. Validate presence of both
    if not file_type or not transport_num:
        raise ValueError(
            f"Could not determine valid file or transport types for path: '{file_path}'"
        )

    # 4. Get transport name from dictionary
    transport_str = transports.get(transport_num)
    if not transport_str:
        raise ValueError(
            f"Transport number '{transport_num}' not found in dictionary: {transports}"
        )

    # 5. Normalise transport string
    transport_str = transport_str.replace(' ', '_').lower()

    return file_type, transport_str


def get_keep_file_basenames() -> list[str]:
    """
    Return the base names (without extensions) of GTFS Schedule files that are kept.

    Example:
        ['stops.txt', 'routes.txt'] → ['stops', 'routes']
    """
    files = []

    for file in TRANSPORTS.values():
        if file in files:
            break
        else:
            files.extend(file)

    return [Path(file).stem for file in files]