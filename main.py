from bs4 import BeautifulSoup
import re
import requests

# 1. Get HTML of GTFS Schedule
url = "https://opendata.transport.vic.gov.au/dataset/gtfs-schedule"
response = requests.get(url)

# 2. Parse response to get download link
soup = BeautifulSoup(response.text, features="html.parser")
filtered = soup.find_all("a", attrs={"href": re.compile("gtfs.zip")})       # Gets the tags where the gtfs.zip is
links = [a.get('href') for a in filtered]       # Extract the href links
downloadLink = ""

if len(links) > 0:
    downloadLink = links[0]

# 3. Download the file

# 4. Get the necessary files
