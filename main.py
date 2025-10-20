import os
from datetime import datetime

from bs4 import BeautifulSoup
import re
import requests
from gtfs import downloadGtfs, cleanGtfs, updateLastUpdated, getLastUpdatedDate, date_format, add_to_database
from utils import reset, delete_file

# FLAG TO ENABLE/DISABLE DOWNLOADS
ENABLE_DOWNLOAD = True
RESET_FILES = False

# 1. Get HTML of GTFS Schedule
url = "https://opendata.transport.vic.gov.au/dataset/gtfs-schedule"
response = requests.get(url)

# 2. Parse response to get download link and specific folder numbers
soup = BeautifulSoup(response.text, features="html.parser")

previousDate = getLastUpdatedDate()
dateFilter = soup.find("th", string="Last Updated Date")
dateString = dateFilter.find_next("td").get_text(strip=True)
newDate = datetime.strptime(dateString, date_format)
print(f"Date of new data: {newDate}")

# Stop if newDate is older than or equal to previousDate
if previousDate and (newDate <= previousDate):
    # do nothing
    print("New data is not newer than previous data, skipping")
else:
    print("Updating data")
    updateLastUpdated(dateString)

    # Download link
    downloadFilter = soup.find_all("a", attrs={"href": re.compile("gtfs.zip")})       # Gets the tags where the gtfs.zip is
    links = [a.get('href') for a in downloadFilter]       # Extract the href links
    downloadLink = ""
    if len(links) > 0:
        downloadLink = links[0]

    # Transport Types
    # transports = "Metropolitan"       # Folder numbers for metro Tram, Train, Bus
    transports = "Tram"
    numberFilter = soup.find_all("p")
    transportsDict = {}

    pattern = r"(\d+)\s*\(([^)]+)\)"        # assumes the transport type is of the form: "number (transport type)", ex "3 (Metropolitan Tram)"
    for item in numberFilter:
        if item.getText().__contains__(transports):
            transport = item.getText()
            match = re.findall(pattern, transport)

            if len(match) > 0:
                number = match[0][0]
                transportType = match[0][1]
                transportsDict[number] = transportType

    print(f"Transports dictionary: {transportsDict}")

    # 3. Download the file
    gtfsFile = "gtfs.zip"
    downloadGtfs(downloadLink, gtfsFile, ENABLE_DOWNLOAD)

    # 4. Get the necessary files
    extractedDirectory = "extracted"
    keepFolders = list(transportsDict.keys())
    keepFiles = ["routes.txt", "trips.txt", "shapes.txt"]

    cleanGtfs(gtfsFile, extractedDirectory, keepFolders, keepFiles, ENABLE_DOWNLOAD)

    # 5. Convert to sqlite database
    database = "gtfs.sqlite"
    delete_file(database)      # delete table, if it exists
    for root, dirs, files in os.walk("extracted"):
        for filename in files:
            data_file_path = os.path.join(root, filename)

            if ".txt" in data_file_path:
                add_to_database(database, data_file_path, transportsDict)

    # 6. Delete the downloaded gtfs.zip and extracted files to save space
    delete_file(gtfsFile)
    delete_file(extractedDirectory)

print("Done")

# Test. Reset files
reset(RESET_FILES)
