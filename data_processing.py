import os
from datetime import datetime
from bs4 import BeautifulSoup
import re
import requests
from requests import Response

from gtfs import download_gtfs, clean_gtfs, date_format
from database import update_data_version, get_data_version, delete_old_data, \
    is_db_connected, add_gtfs_site_log, add_to_database
from utils import delete_file
from config import GTFS_FILE, EXTRACTED_DIRECTORY, IGNORE_VERSION_CHECK, MOCK_OLD_DATE, OLD_DATE, \
    GTFS_URL, MyFile, TRANSPORTS
from cloud import upload_string_to_cloud_storage


def update_gtfs_data():
    """
    Main function to update GTFS data.
    Downloads new data if available and builds database.

    Returns:
        tuple: True if data was updated, False if not, and Date of Data
    """
    print("======= Starting GTFS Update Process =======")

    # Open MongoDB and check status
    if not is_db_connected():
        raise Exception("MongoDB unreachable, could not update GTFS data")

    # Fetch metadata
    data_version, download_link, soup = fetch_gtfs_data()

    # Check if update needed
    if not check_if_update_needed(data_version):
        return False

    # Update last updated date in the database (and site metadata in logs)
    update_data_version(data_version)
    site_version, metadata_version = fetch_site_metadata()
    add_gtfs_site_log(data_version, site_version, metadata_version)

    # Parse transport types
    transports_dict = parse_transport_types(soup, list(TRANSPORTS.keys()))

    # Download and process gtfs schedule files
    download_and_extract_gtfs(download_link, transports_dict)

    # Build database
    build_database(transports_dict)

    # Cleanup
    delete_old_data(data_version)

    return True


def fetch_gtfs_data() -> tuple[datetime, str, BeautifulSoup]:
    """
    Fetch the GTFS dataset page and extract metadata.

    Returns:
        tuple: (version_date, download_link, soup object)
    """
    headers = {
        'User-Agent': 'GTFS-Schedule-Updater/1.0 (Educational/Research Project)',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
    }

    response = requests.get(GTFS_URL, headers=headers, timeout=30)
    soup = BeautifulSoup(response.text, features="html.parser")

    upload_string_to_cloud_storage("gtfs.html", response.text)

    # 1. Extract version date
    date_filter = soup.find("th", string="Last Updated Date")
    date_string = date_filter.find_next("td").get_text(strip=True)
    version_date = datetime.strptime(date_string, date_format)

    # Test
    if MOCK_OLD_DATE:
        version_date = OLD_DATE
        print("[TEST] Using mocked old date")

    # 2. Extract download link
    download_filter = soup.find_all("a", attrs={"href": re.compile("gtfs.zip")})
    links = [a.get('href') for a in download_filter]

    if not links:
        raise ValueError("Could not find GTFS download link on the page")

    download_link = links[0] if links else ""

    return version_date, download_link, soup


def fetch_site_metadata() -> tuple[datetime | None, datetime | None]:
    """
    Fetches the last update timestamps for the GTFS site metadata from the Transport Victoria API.

    Returns:
        tuple[datetime | None, datetime | None]: A tuple containing:
            - last_updated_date: The date the site was last updated.
            - metadata_modified: The date the metadata was last modified.
            Returns None for either value if fetching or parsing fails.
    """
    url = "https://opendata.transport.vic.gov.au/api/3/action/package_show"
    params = {"id": "gtfs-schedule"}

    response: Response = requests.get(url, params=params)
    data = response.json()
    result = data['result']

    # Convert the data to datetime
    last_updated_date: datetime = datetime.fromisoformat(result['last_updated_date'])
    metadata_modified: datetime = datetime.fromisoformat(result['metadata_modified'])
    print(f"Site last updated: {last_updated_date} | Metadata last updated: {metadata_modified}")

    return last_updated_date, metadata_modified


def parse_transport_types(soup: BeautifulSoup, transport_filter: list[str]) -> dict[str, str]:
    """
    Parse transport types and their numbers from the HTML.

    Args:
        soup (BeautifulSoup): Parsed HTML document
        transport_filter (str): String to filter transport types (e.g., "Tram", "Metro", etc.)

    Returns:
        dict: {transport_number: transport_type}
    """
    transports_dict = {}
    # pattern = r"(\d+)\s*\(([^)]+)\)"      # this pattern used to work for example: "4 (Metropolitan Bus)"
    pattern = r"(\d+)\s*(?:\(([^)]+)\)|(.+))"   # But now they changed bus to a different format: "4 Myki Bus (Metro Bus and Regional Town Bus)"
    p_filter = soup.find_all("p")

    for item in p_filter:
        if any(search in item.getText() for search in transport_filter):
            transport = item.getText()
            match = re.search(pattern, transport)

            if match:
                transport_number = match.group(1)
                transport_type = match.group(2) or match.group(3)

                # Hardcoded case for Bus
                if "metro bus" in transport_type.lower():
                    transport_type = "Metro Bus"

                transports_dict[transport_number] = transport_type

    print(f"Transports dictionary: {transports_dict}")
    return transports_dict


def check_if_update_needed(new_date: datetime) -> bool:
    """
    Check if data needs updating based on dates.

    Args:
        new_date: datetime object of new data

    Returns:
        bool: True if update needed, False otherwise
    """
    if IGNORE_VERSION_CHECK:
        print("[TEST] Skipping version check")
        return True

    previous_date: datetime = get_data_version()
    print(f"Old data version: {previous_date}")
    print(f"New data version: {new_date}")

    if previous_date and (new_date <= previous_date):
        print("New data is not newer than previous data, skipping...")
        return False

    print("Updating data")
    return True


def download_and_extract_gtfs(download_link: str, transports_dict: dict[str,str]) -> None:
    """
    Download GTFS file and extract relevant transport data.

    Args:
        download_link (str): URL to download GTFS zip
        transports_dict (dict[str,str]): Dictionary of transports and their corresponding numbers and types
    """
    # Download
    download_gtfs(download_link, GTFS_FILE)

    # Extract
    clean_gtfs(GTFS_FILE, EXTRACTED_DIRECTORY, transports_dict)

    # Delete gtfs zip file
    delete_file(GTFS_FILE)


def build_database(transports_dict: dict[str,str]) -> None:
    """
    Build database from extracted GTFS files.

    Args:
        transports_dict: Dictionary of transport numbers and types
    """

    # Process all extracted txt files, and delete them afterwards
    for root, dirs, files in os.walk(EXTRACTED_DIRECTORY.path):
        for filename in files:
            data_file_path = MyFile(os.path.join(root, filename))

            if data_file_path.name.endswith(".txt"):
                add_to_database(data_file_path, transports_dict)
                delete_file(data_file_path)

    delete_file(EXTRACTED_DIRECTORY)
