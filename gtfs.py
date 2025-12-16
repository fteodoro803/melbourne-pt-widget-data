import os
import zipfile

import requests
import io

from config import MyFile, SKIP_DOWNLOAD, TRANSPORTS

date_format = "%d %B %Y"  # matches "19 September 2025"

def download_gtfs(download_link: str, file: MyFile) -> None:
    """
    Download a GTFS ZIP file from a URL.

    Parameters:
        download_link (str): URL to download the GTFS file.
        file (MyFile): Name to save the downloaded file as.
    """

    if SKIP_DOWNLOAD:
        print("[TEST] Skipping download")
        return

    # Stream download in chunks to avoid loading the whole file into memory
    with requests.get(download_link, stream=True) as r:
        r.raise_for_status()  # Raise an error if the request failed
        with open(file.path, 'wb') as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)

    print(f"Downloaded {file}")

def clean_gtfs(gtfs_zip: MyFile, output_folder: MyFile, transport_dict: dict[str,str]) -> None:
    """
    Extract selected files from inner ZIPs inside a GTFS outer ZIP.

    Parameters:
        gtfs_zip (MyFile): Path to the outer GTFS ZIP file.
        output_folder (MyFile): Base folder where extracted files will go.
        transport_dict (dict[str,str]): Only process these modes of transportation.
    """
    # Ensures output folder exists
    os.makedirs(output_folder.path, exist_ok=True)

    # 1. Open outer GTFS zip file
    with zipfile.ZipFile(gtfs_zip.path, 'r') as gtfsRead:

        # 2. Iterate over all files in the zip
        print("Saving files...")
        for transport in gtfsRead.namelist():
            transport_number = transport.split('/')[0]      # first part of the path, e.g. '2'

            # Only process if in keep_folders and is a .zip file
            if transport_number in transport_dict and transport.endswith(".zip"):
                transport_name = transport_dict[transport_number]

                # 3. Create subfolder for the transport number
                subfolder = os.path.join(output_folder.path, transport_number)
                os.makedirs(subfolder, exist_ok=True)

                # 4. Read the zip file within the Transport Number's directory
                inner_data = gtfsRead.read(transport)

                with zipfile.ZipFile(io.BytesIO(inner_data), 'r') as transitRead:
                    for file in transitRead.namelist():

                        # 5. Save the files specified in keep_files
                        if file in TRANSPORTS[transport_name]:
                            data = transitRead.read(file)
                            out_path = os.path.join(subfolder, file)

                            # Save to disk
                            with open(out_path, 'wb') as f:
                                f.write(data)

                            print(f"        {file} from {transport} to {out_path}")
