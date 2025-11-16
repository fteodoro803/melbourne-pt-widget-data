from datetime import datetime
from bs4 import BeautifulSoup
import re
import requests

from gtfs import download_gtfs, clean_gtfs, date_format
from database import add_gtfs_data, update_data_version, get_data_version, delete_old_data, \
    is_db_connected
from utils import delete_file
from config import GTFS_FILE, EXTRACTED_DIRECTORY, KEEP_TEMP_FILES, IGNORE_VERSION_CHECK, MOCK_OLD_DATE, OLD_DATE, \
    GTFS_URL, TRANSPORT_FILTER, KEEP_FILES
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
    data_version, download_link, soup = fetch_gtfs_metadata()

    # Check if update needed
    if not check_if_update_needed(data_version):
        return False

    # Update last updated date
    update_data_version(data_version)

    # Parse transport types
    transports_dict = parse_transport_types(soup, TRANSPORT_FILTER)

    # Download and process gtfs schedule files
    download_and_extract_gtfs(download_link, transports_dict)

    # Build database
    add_gtfs_data(transports_dict)

    # Cleanup
    delete_old_data(data_version)
    cleanup_temp_files()

    return True


def fetch_gtfs_metadata() -> tuple[datetime, str, BeautifulSoup]:
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


def parse_transport_types(soup: BeautifulSoup, transport_filter: str) -> dict[str, str]:
    """
    Parse transport types and their numbers from the HTML.

    Args:
        soup (BeautifulSoup): Parsed HTML document
        transport_filter (str): String to filter transport types (e.g., "Tram", "Metro", etc.)

    Returns:
        dict: {transport_number: transport_type}
    """
    transports_dict = {}
    pattern = r"(\d+)\s*\(([^)]+)\)"
    number_filter = soup.find_all("p")

    for item in number_filter:
        if transport_filter in item.getText():
            transport = item.getText()
            match = re.findall(pattern, transport)

            if match:
                transport_number = match[0][0]
                transport_type = match[0][1]
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

    previous_date = get_data_version()
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
    keep_folders = list(transports_dict.keys())
    clean_gtfs(GTFS_FILE, EXTRACTED_DIRECTORY, keep_folders, KEEP_FILES)


def cleanup_temp_files() -> None:
    """Remove temporary files to save space."""
    if KEEP_TEMP_FILES:
        print("[TEST] Skipping cleanup of temporary files")
        return

    delete_file(GTFS_FILE)
    delete_file(EXTRACTED_DIRECTORY)
