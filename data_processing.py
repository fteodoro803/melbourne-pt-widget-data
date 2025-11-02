import os
from datetime import datetime

from bs4 import BeautifulSoup
import re
import requests

from gtfs import download_gtfs, clean_gtfs, update_version, get_version, date_format, add_to_database
from utils import reset, delete_file
from config import GTFS_FILE, DATABASE_FILE, EXTRACTED_DIRECTORY
from cloud import upload_generic_to_cloud_storage

# Constants
GTFS_URL = "https://opendata.transport.vic.gov.au/dataset/gtfs-schedule"
TRANSPORT_FILTER = "Tram"  # Can be "Metropolitan", "Tram", etc.
KEEP_FILES = ["routes.txt", "trips.txt", "shapes.txt"]


def fetch_gtfs_metadata() -> tuple[datetime, str, BeautifulSoup]:
    """
    Fetch the GTFS dataset page and extract metadata.

    Returns:
        tuple: (version_date, download_link, soup object)
    """
    response = requests.get(GTFS_URL)
    soup = BeautifulSoup(response.text, features="html.parser")

    upload_generic_to_cloud_storage("gtfs.html", response.text)

    # Extract version date
    date_filter = soup.find("th", string="Last Updated Date")
    date_string = date_filter.find_next("td").get_text(strip=True)
    version_date = datetime.strptime(date_string, date_format)

    # Extract download link
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
    previous_date = get_version()
    print(f"Date of new data: {new_date}")

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


def build_database(transports_dict: dict[str,str]) -> None:
    """
    Build SQLite database from extracted GTFS files.

    Args:
        transports_dict: Dictionary of transport numbers and types
    """
    # Delete old database
    delete_file(DATABASE_FILE)

    # Process all extracted txt files
    for root, dirs, files in os.walk(EXTRACTED_DIRECTORY.path):
        for filename in files:
            data_file_path = os.path.join(root, filename)

            if data_file_path.endswith(".txt"):
                add_to_database(DATABASE_FILE, data_file_path, transports_dict)


def cleanup_temp_files() -> None:
    """Remove temporary files to save space."""
    delete_file(GTFS_FILE)
    delete_file(EXTRACTED_DIRECTORY)


def update_gtfs_data():
    """
    Main function to update GTFS data.
    Downloads new data if available and builds database.

    Returns:
        tuple: True if data was updated, False if not, and Date of Data
    """
    # Fetch metadata
    data_version, download_link, soup = fetch_gtfs_metadata()

    # Check if update needed
    if not check_if_update_needed(data_version):
        return False, data_version

    # Update last updated date
    update_version(data_version.strftime(date_format))

    # Parse transport types
    transports_dict = parse_transport_types(soup, TRANSPORT_FILTER)

    # Download and process gtfs schedule files
    download_and_extract_gtfs(download_link, transports_dict)

    # Build database
    build_database(transports_dict)

    # Cleanup
    cleanup_temp_files()

    return True, data_version


def main():
    """Entry point for local testing."""
    RESET_FILES = False

    try:
        update_gtfs_data()
        print("Done")
    except Exception as e:
        print(f"Error: {e}")
        raise
    finally:
        # Test reset if needed
        reset(RESET_FILES)


if __name__ == "__main__":
    main()