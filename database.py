import os
import re
import pandas as pd

from datetime import datetime
from pymongo import MongoClient
from pymongo.server_api import ServerApi
from config import EXTRACTED_DIRECTORY

# Mongo
MONGO_PASSWORD = "1wxN24DvwXKy55yV"     # todo: change password then make it a secret probably
uri = f"mongodb+srv://fernandoagustin803_db_user:{MONGO_PASSWORD}@cluster0.kubarsp.mongodb.net/?appName=Cluster0"
client = MongoClient(uri, server_api=ServerApi('1'))

def build_database(transports_dict: dict[str,str]) -> None:
    """
    Build MongoDB database from extracted GTFS files.

    Args:
        transports_dict: Dictionary of transport numbers and types
    """

    # Process all extracted txt files
    for root, dirs, files in os.walk(EXTRACTED_DIRECTORY.path):
        for filename in files:
            data_file_path = os.path.join(root, filename)

            if data_file_path.endswith(".txt"):
                add_to_database(data_file_path, transports_dict)


def add_to_database(file_path: str, transports: dict[str, str]) -> None:
    try:
        # 1. Select database
        db = client.gtfs

        # 2. Load file
        df = pd.read_csv(file_path)

        # 3. Figure out file type
        file_type = ""
        collection = None
        if "trips.txt" in file_path:
            file_type = "trips"
            collection = db.trips
        elif "routes.txt" in file_path:
            file_type = "routes"
            collection = db.routes
        elif "shapes.txt" in file_path:
            file_type = "shapes"
            collection = db.shapes

        # 4. Find transport type
        transport_num = re.search(r'\d+', file_path)
        if len(file_type) == 0 or transport_num is None:
            return

        if transport_num:
            transport_num = transport_num.group()       # converts to a str
            transport_str = transports[transport_num]
        else:
            return

        transport_str = transport_str.replace(' ', '_').lower()

        # 5. Dataframe modifications
        # todo: remove NaN
        # add version to data entries

        # 6. Save file dataframe to database
        # df['version'] = version   #todo: get version from misc
        records = df.to_dict('records')
        if collection is not None:
            collection.insert_many(records)
            print(f"Added {transport_str}_{file_type} to mongoDB database")

    except Exception as e:
        print(e)

def update_data_version(version: datetime) -> None:
    try:
        # 1. Select database and collection
        db = client.gtfs
        collection = db.misc

        # 2. Upsert data
        collection.update_one(
            {"_id": "gtfs_version"},            # match any document (or none)
            {"$set": {"version": version}},     # update this field
            upsert=True                         # insert if no document exists
        )

    except Exception as e:
        print(e)

def get_data_version() -> datetime:
    try:
        db = client.gtfs
        collection = db.misc

        document = collection.find_one({"_id": "gtfs_version"})
        if document and "version" in document:
            version: datetime = document["version"]
            return version

    except Exception as e:
        print(e)

def close_database() -> None:
    client.close()