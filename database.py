import os
import certifi
import pandas as pd
import numpy as np

from datetime import datetime
from pymongo import MongoClient
from pymongo.database import Database
from pymongo.server_api import ServerApi
from pymongo.synchronous.collection import Collection

from config import EXTRACTED_DIRECTORY, KEEP_OUTDATED_DATA, MONGO_URI, MONGO_DATABASE
from utils import get_types_from_path, get_keep_file_basenames

# Mongo
client = MongoClient(
    MONGO_URI,
    server_api=ServerApi('1'),
    tlsCAFile = certifi.where(),
)

def is_db_connected() -> bool:
    try:
        client.admin.command("ping")
        print("Connected to MongoDB")
        return True
    except Exception as e:
        print("Could not connect to MongoDB")
        print(f"     Error: {e}")
        return False

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
        db: Database= client[MONGO_DATABASE]

        # 2. Load file
        df = pd.read_csv(file_path)

        # 3. Determine file and transport types to access target collection
        file_type, transport_type = get_types_from_path(file_path, transports)
        collection: Collection= db[f"{transport_type}_{file_type}"]

        # 4. Dataframe modifications
        df = df.replace({np.nan: None})         # remove NaN
        df['version'] = get_data_version()      # add version to fields

        # 5. Save file dataframe to database
        records = df.to_dict('records')
        time_start = datetime.now()
        print(f"Inserting {len(records)} records to {transport_type}_{file_type}...")

        # Insertion logic
        if collection is not None:
            collection.insert_many(records, ordered=False)

        time_difference = (datetime.now() - time_start).seconds
        print(f"        Successfully added records, took {time_difference} seconds")

    except Exception as e:
        print(e)

def update_data_version(version: datetime) -> None:
    try:
        # 1. Select database and collection
        db: Database = client[MONGO_DATABASE]
        collection: Collection= db.misc

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
        db: Database= client[MONGO_DATABASE]
        collection: Collection= db.misc

        document = collection.find_one({"_id": "gtfs_version"})
        if document and "version" in document:
            version: datetime = document["version"]
            return version

    except Exception as e:
        print(e)

def delete_old_data(version: datetime) -> None:
    if KEEP_OUTDATED_DATA:
        print("[TEST] Keeping outdated data")
        return

    try:
        # 1. Select database'
        db: Database = client[MONGO_DATABASE]

        # 2. Get a list of Collections and iterate through them
        collections = db.list_collection_names()
        saved_gtfs_folders = get_keep_file_basenames()
        # print(f"Collections: {collections} | Saved GTFS Folders: {saved_gtfs_folders}")

        # Keep only collections that contain any of the saved GTFS folder names
        collections = [
            c for c in collections
            if any(folder in c for folder in saved_gtfs_folders)
        ]
        # print(f"Filtered Collections: {collections}")

        for collection_name in collections:
            collection = db[collection_name]
            time_start = datetime.now()

            # 3. Delete outdated documents
            filter_query = {"version": {"$lt": version}}
            deletion_count = collection.count_documents(filter_query)

            if deletion_count > 0:
                print(f"Deleting {deletion_count} outdated records from {collection_name}...")

                collection.delete_many(filter_query)
                total_time = (datetime.now() - time_start).seconds
                print(f"        Successfully deleted outdated records, took {total_time} seconds")
            else:
                print(f"No outdated records in {collection_name}")

    except Exception as e:
        print(e)

def close_database() -> None:
    client.close()