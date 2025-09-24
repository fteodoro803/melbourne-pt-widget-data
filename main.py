from bs4 import BeautifulSoup
import re
import requests
from gtfs import downloadGtfs, cleanGtfs

ENABLE_DOWNLOAD = True

# 1. Get HTML of GTFS Schedule
url = "https://opendata.transport.vic.gov.au/dataset/gtfs-schedule"
response = requests.get(url)

# 2. Parse response to get download link and specific folder numbers
soup = BeautifulSoup(response.text, features="html.parser")

# Download link
downloadFilter = soup.find_all("a", attrs={"href": re.compile("gtfs.zip")})       # Gets the tags where the gtfs.zip is
links = [a.get('href') for a in downloadFilter]       # Extract the href links
downloadLink = ""
if len(links) > 0:
    downloadLink = links[0]

# Folder numbers for metro Tram, Train, Bus
transports = "Metropolitan"
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
fileName = "gtfs.zip"
downloadGtfs(downloadLink, fileName, ENABLE_DOWNLOAD)

# 4. Get the necessary files
extractTo = "extracted"
keepFolders = list(transportsDict.keys())
keepFiles = ["routes.txt", "trips.txt", "shapes.txt"]

cleanGtfs(fileName, extractTo, keepFolders, keepFiles, ENABLE_DOWNLOAD)
