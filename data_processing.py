import os
from datetime import datetime

from bs4 import BeautifulSoup
import re
import requests
from pyasn1.type.univ import Boolean

from gtfs import downloadGtfs, cleanGtfs, updateLastUpdated, getLastUpdatedDate, date_format, add_to_database
from utils import reset, delete_file
from files import GTFS_FILE, DATABASE_FILE, EXTRACTED_DIRECTORY

# Constants
GTFS_URL = "https://opendata.transport.vic.gov.au/dataset/gtfs-schedule"
TRANSPORT_FILTER = "Tram"  # Can be "Metropolitan", "Tram", etc.
KEEP_FILES = ["routes.txt", "trips.txt", "shapes.txt"]


def fetch_gtfs_metadata():
    """
    Fetch the GTFS dataset page and extract metadata.

    Returns:
        tuple: (last_updated_date, download_link, soup object)
    """
    response = requests.get(GTFS_URL)
    soup = BeautifulSoup(response.text, features="html.parser")

    # Extract last updated date
    dateFilter = soup.find("th", string="Last Updated Date")
    dateString = dateFilter.find_next("td").get_text(strip=True)
    lastUpdated = datetime.strptime(dateString, date_format)

    # Extract download link
    downloadFilter = soup.find_all("a", attrs={"href": re.compile("gtfs.zip")})
    links = [a.get('href') for a in downloadFilter]
    downloadLink = links[0] if links else ""

    return lastUpdated, downloadLink, soup


def parse_transport_types(soup, transport_filter):
    """
    Parse transport types and their numbers from the HTML.

    Args:
        soup: BeautifulSoup object
        transport_filter: String to filter transport types (e.g., "Tram")

    Returns:
        dict: {transport_number: transport_type}
    """
    transportsDict = {}
    pattern = r"(\d+)\s*\(([^)]+)\)"
    numberFilter = soup.find_all("p")

    for item in numberFilter:
        if transport_filter in item.getText():
            transport = item.getText()
            match = re.findall(pattern, transport)

            if match:
                number = match[0][0]
                transportType = match[0][1]
                transportsDict[number] = transportType

    print(f"Transports dictionary: {transportsDict}")
    return transportsDict


def check_if_update_needed(new_date):
    """
    Check if data needs updating based on dates.

    Args:
        new_date: datetime object of new data

    Returns:
        bool: True if update needed, False otherwise
    """
    previousDate = getLastUpdatedDate()
    print(f"Date of new data: {new_date}")

    if previousDate and (new_date <= previousDate):
        print("New data is not newer than previous data, skipping...")
        return False

    print("Updating data")
    return True


def download_and_extract_gtfs(download_link, transports_dict):
    """
    Download GTFS file and extract relevant transport data.

    Args:
        download_link: URL to download GTFS zip
        transports_dict: Dictionary of transport numbers and types
    """
    # Download
    downloadGtfs(download_link, GTFS_FILE, enabled=True)

    # Extract
    keepFolders = list(transports_dict.keys())
    cleanGtfs(GTFS_FILE, EXTRACTED_DIRECTORY, keepFolders, KEEP_FILES, enabled=True)


def build_database(transports_dict):
    """
    Build SQLite database from extracted GTFS files.

    Args:
        transports_dict: Dictionary of transport numbers and types
    """
    # Delete old database
    delete_file(DATABASE_FILE)

    # Process all extracted txt files
    for root, dirs, files in os.walk(EXTRACTED_DIRECTORY):
        for filename in files:
            data_file_path = os.path.join(root, filename)

            if data_file_path.endswith(".txt"):
                add_to_database(DATABASE_FILE, data_file_path, transports_dict)


def cleanup_temp_files():
    """Remove temporary files to save space."""
    delete_file(GTFS_FILE)
    delete_file(EXTRACTED_DIRECTORY)


def update_gtfs_data():
    """
    Main function to update GTFS data.
    Downloads new data if available and builds database.

    Returns:
        bool: True if update was performed, False if skipped
    """
    # Fetch metadata
    dateOfData, downloadLink, soup = fetch_gtfs_metadata()

    # Check if update needed
    if not check_if_update_needed(dateOfData):
        return False, dateOfData

    # Update last updated date
    updateLastUpdated(dateOfData.strftime(date_format))

    # Parse transport types
    transportsDict = parse_transport_types(soup, TRANSPORT_FILTER)

    # Download and process
    download_and_extract_gtfs(downloadLink, transportsDict)

    # Build database
    build_database(transportsDict)

    # Cleanup
    cleanup_temp_files()

    return True, dateOfData


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