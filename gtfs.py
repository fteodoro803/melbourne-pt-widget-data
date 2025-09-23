import requests

def downloadGtfs(downloadLink, fileName, enabled):
    if not enabled:
        return

    with requests.get(downloadLink, stream=True) as r:
        r.raise_for_status()  # Raise an error if the request failed
        with open(fileName, 'wb') as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)

    print(f"Downloaded {fileName}")