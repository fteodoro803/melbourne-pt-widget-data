import os
import re
import zipfile
from datetime import datetime

import requests
import io

import pandas as pd
import sqlite3

from files import LAST_UPDATED_FILE

date_format = "%d %B %Y"  # matches "19 September 2025"

# -----------------------------------
# Updates last_updated.txt
# -----------------------------------
def update_version(date_of_data: str) -> None:
    try:
        with open(LAST_UPDATED_FILE, "w") as f:
            f.write(date_of_data.__str__())

        print(f"Created/Updated {LAST_UPDATED_FILE} with date: {date_of_data}")
    except FileNotFoundError:
        print(f"No {LAST_UPDATED_FILE} found.")
        return None

def get_version() -> datetime | None:
    try:
        with open(LAST_UPDATED_FILE, "r") as f:
            data = f.read()
            date = datetime.strptime(data, date_format)
            print(f"Date of old data: {date}")
            return date
    except FileNotFoundError:
        print(f"No {LAST_UPDATED_FILE} found.")
        return None

# -----------------------------------
# Download the GTFS Schedule ZIP file
# -----------------------------------
def download_gtfs(download_link: str, file_name: str) -> None:
    """
    Download a GTFS ZIP file from a URL.

    Parameters:
        download_link (str): URL to download the GTFS file.
        file_name (str): Name to save the downloaded file as.
    """

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
def clean_gtfs(gtfs_zip: str, output_folder: str, keep_folders: [str], keep_files: [str]) -> None:
    """
    Extract selected files from inner ZIPs inside a GTFS outer ZIP.

    Parameters:
        gtfs_zip (str): Path to the outer GTFS ZIP file.
        output_folder (str): Base folder where extracted files will go.
        keep_folders (list[str]): Only process these transport numbers (e.g. ['2','3']).
        keep_files (list[str]): Only extract these filenames from each inner ZIP (e.g. ['routes.txt','stops.txt']).
    """

    # Ensures output folder exists
    os.makedirs(output_folder, exist_ok=True)

    # 1. Open outer GTFS zip file
    with zipfile.ZipFile(gtfs_zip, 'r') as gtfsRead:

        # 2. Iterate over all files in the zip
        for transport in gtfsRead.namelist():
            transport_number = transport.split('/')[0]      # first part of the path, e.g. '2'

            # Only process if in keep_folders and is a .zip file
            if transport_number in keep_folders and transport.endswith(".zip"):

                # 3. Create subfolder for the transport number
                subfolder = os.path.join(output_folder, transport_number)
                os.makedirs(subfolder, exist_ok=True)

                # 4. Read the zip file within the Transport Number's directory
                inner_data = gtfsRead.read(transport)

                with zipfile.ZipFile(io.BytesIO(inner_data), 'r') as transitRead:
                    for file in transitRead.namelist():

                        # 5. Save the files specified in keep_files
                        if file in keep_files:
                            data = transitRead.read(file)
                            out_path = os.path.join(subfolder, file)

                            # Save to disk
                            with open(out_path, 'wb') as f:
                                f.write(data)

                            print(f"Saved {file} from {transport} to {out_path}")

def add_to_database(database: str, file_path: str, transports: dict[str, str]) -> None:
    # 1. Load file
    df = pd.read_csv(file_path)

    # 2. Figure out file type
    file_type = ""
    if "trips.txt" in file_path:
        file_type = "trips"
    elif "routes.txt" in file_path:
        file_type = "routes"
    elif "shapes.txt" in file_path:
        file_type = "shapes"

    # 3. Find transport type
    transport_num = re.search(r'\d+', file_path)
    if len(file_type) == 0 or transport_num is None:
        return

    if transport_num:
        transport_num = transport_num.group()       # converts to a str
        transport_str = transports[transport_num]
    else:
        return

    transport_str = transport_str.replace(' ', '_').lower()

    # 4. Create/Open database
    database = sqlite3.connect(database)

    # 5. Save file dataframe to database
    df.to_sql(f"{transport_str}_{file_type}", database, if_exists="replace", index=False)
    print(f"Added {transport_str}_{file_type} to database")