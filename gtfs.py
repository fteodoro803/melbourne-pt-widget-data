import os
import zipfile
from datetime import datetime

import requests
import io
import shutil

last_updated_file = "last_updated.txt"
date_format = "%d %B %Y"  # matches "19 September 2025"

# -----------------------------------
# Updates last_updated.txt
# -----------------------------------
def updateLastUpdated(date_of_data: str) -> None:
    with open(last_updated_file, "w") as f:
        f.write(date_of_data.__str__())

    print(f"Updated {last_updated_file} with date: {date_of_data}")

def getLastUpdatedDate() -> datetime | None:

    try:
        with open(last_updated_file, "r") as f:
            data = f.read()
            date = datetime.strptime(data, date_format)
            print(f"Date of old data: {date}")
            return date
    except FileNotFoundError:
        print(f"No {last_updated_file} found.")
        return None

# -----------------------------------
# Download the GTFS Schedule ZIP file
# -----------------------------------
def downloadGtfs(download_link: str, file_name: str, enabled: bool) -> None:
    """
    Download a GTFS ZIP file from a URL.

    Parameters:
        download_link (str): URL to download the GTFS file.
        file_name (str): Name to save the downloaded file as.
        enabled (bool): If False, skip downloading.
    """

    # Skip if disabled
    if not enabled:
        return

    # Stream download in chunks to avoid loading the whole file into memory
    with requests.get(download_link, stream=True) as r:
        r.raise_for_status()  # Raise an error if the request failed
        with open(file_name, 'wb') as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)

    print(f"Downloaded {file_name}")


# -----------------------------------
# Extract selected files from GTFS ZIP
# -----------------------------------
def cleanGtfs(gtfs_zip: str, output_folder: str, keep_folders: [str], keep_files: [str], enabled: bool) -> None:
    """
    Extract selected files from inner ZIPs inside a GTFS outer ZIP.

    Parameters:
        gtfs_zip (str): Path to the outer GTFS ZIP file.
        output_folder (str): Base folder where extracted files will go.
        keep_folders (list[str]): Only process these transport numbers (e.g. ['2','3']).
        keep_files (list[str]): Only extract these filenames from each inner ZIP (e.g. ['routes.txt','stops.txt']).
        enabled (bool):
    """

    # Skip if disabled
    if not enabled:
        return

    # Ensures output folder exists
    os.makedirs(output_folder, exist_ok=True)

    # 1. Open outer GTFS zip file
    with zipfile.ZipFile(gtfs_zip, 'r') as gtfsRead:

        # 2. Iterate over all files in the zip
        for transport in gtfsRead.namelist():
            transportNumber = transport.split('/')[0]      # first part of the path, e.g. '2'

            # Only process if in keep_folders and is a .zip file
            if transportNumber in keep_folders and transport.endswith(".zip"):

                # 3. Create subfolder for the transport number
                subFolder = os.path.join(output_folder, transportNumber)
                os.makedirs(subFolder, exist_ok=True)

                # 4. Read the zip file within the Transport Number's directory
                innerData = gtfsRead.read(transport)

                with zipfile.ZipFile(io.BytesIO(innerData), 'r') as transitRead:
                    for file in transitRead.namelist():

                        # 5. Save the files specified in keep_files
                        if file in keep_files:
                            data = transitRead.read(file)
                            out_path = os.path.join(subFolder, file)

                            # Save to disk
                            with open(out_path, 'wb') as f:
                                f.write(data)

                            print(f"Saved {file} from {transport} to {out_path}")

def delete_file(path: str) -> None:
    """
    Delete a file or directory (recursively if directory).
    """
    if os.path.isdir(path):
        shutil.rmtree(path)
        print(f"Deleted directory {path}")
    elif os.path.isfile(path):
        os.remove(path)
        print(f"Deleted file {path}")
    else:
        print(f"{path} does not exist")

def reset(enabled: bool) -> None:
    if not enabled:
        return

    print(f"Resetting Files")
    print(f"Deleting extracted folder, last_updated.txt, gtfs.zip...")
    delete_file("extracted")
    delete_file("last_updated.txt")
    delete_file("gtfs.zip")
    print("Reset finished")