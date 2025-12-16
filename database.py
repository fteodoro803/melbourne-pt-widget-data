import certifi
import pandas as pd
import numpy as np

from datetime import datetime
from pymongo import MongoClient
from pymongo.database import Database
from pymongo.server_api import ServerApi
from pymongo.synchronous.collection import Collection

from config import KEEP_OUTDATED_DATA, MONGO_URI, MONGO_DATABASE, LOGS_DATABASE, MyFile, MOCK_MONGODB_UNAVAILABLE
from utils import get_types_from_path, get_keep_file_basenames

# Mongo
client: MongoClient = MongoClient(
            MONGO_URI,
            server_api=ServerApi('1'),
            tlsCAFile=certifi.where(),
        )

def is_db_connected() -> bool:
    if MOCK_MONGODB_UNAVAILABLE:
        print("[TEST] Mocking MongoDB unavailable")
        return False

    try:
        client.admin.command("ping")
        print("Connected to MongoDB")
        return True
    except Exception as e:
        print("Could not connect to MongoDB")
        print(f"     Error: {e}")
        return False

def add_to_database(file: MyFile, transports: dict[str, str]) -> None:
    try:
        # 1. Select database
        db: Database= client[MONGO_DATABASE]

        # 2. Load file
        df = pd.read_csv(file.path)

        # 3. Determine file and transport types to access target collection
        file_type, transport_type = get_types_from_path(file.path, transports)
        collection: Collection= db[f"{transport_type}_{file_type}"]

        # 4. Dataframe modifications
        df = df.replace({np.nan: None})         # remove NaN
        df['version'] = get_data_version()      # add version to fields
        if "route_short_name" in df.columns:    # convert route_short_name to string
            df['route_short_name'] = df["route_short_name"].astype(str)

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
            {"$set": {"version": version.isoformat()}},     # update this field
            upsert=True                         # insert if no document exists
        )

    except Exception as e:
        print(e)

def get_data_version() -> datetime:
    try:
        db: Database = client[MONGO_DATABASE]
        collection: Collection = db.misc

        document = collection.find_one({"_id": "gtfs_version"})
        if document and "version" in document:
            version: datetime = datetime.fromisoformat(document["version"])
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

def add_gtfs_site_log(gtfs_last_updated: datetime, site_last_updated: datetime, metadata_modified: datetime) -> None:
    """
    Adds or updates a GTFS site metadata log in the database for tracking updates.

    This function logs the last updated timestamps from the GTFS schedule site and the API.
    If a log entry with the same timestamps exists, it will be updated; otherwise, a new
    entry will be inserted.

    Args:
        gtfs_last_updated (datetime): Date of last update as displayed on the GTFS schedule site.
        site_last_updated (datetime): Date of last update retrieved from the API.
        metadata_modified (datetime): Date when metadata was last modified, retrieved from the API.
    """

    try:
        # 1. Connect to Database and Collection
        db: Database = client[LOGS_DATABASE]
        collection: Collection = db["site_metadata"]

        # 2. Upsert data
        collection.update_one(
            {
                "gtfs_last_updated": gtfs_last_updated,
                "site_last_updated": site_last_updated,
                "metadata_modified": metadata_modified
            },
            {
                "$set": {
                    "gtfs_last_updated": gtfs_last_updated,
                    "site_last_updated": site_last_updated,
                    "metadata_modified": metadata_modified,
                }
            },
            upsert=True
        )

    except Exception as e:
        print(e)

def get_routes():
    try:
        db: Database = client[MONGO_DATABASE]
        collections: list[Collection] = [db[collection] for collection in db.list_collection_names() if "routes" in collection]

        # Go through all collections
        documents = []

        for collection in collections:
            print(f"Collection: {collection}")
            # Get list of all documents, excluding "_id" and "version" field
            documents.extend(list(collection.find({}, {"_id": 0, "version": 0})))

        return documents
    except Exception as e:
        print(e)

def get_shapes(shape_id: str):
    try:
        db: Database = client[MONGO_DATABASE]
        collection: Collection = db["metropolitan_tram_shapes"]

        # Get list of all documents, excluding "_id" and "version" field
        documents = list(collection.find({"shape_id": shape_id}, {"_id": 0, "version": 0}))
        return documents
    except Exception as e:
        print(e)

# Returns the distinct shapes for a specific route
def get_route_shapes(route_id: str) -> list[str]:
    try:
        db: Database = client[MONGO_DATABASE]
        collection: Collection = db["metropolitan_tram_trips"]

        shapes: list[str] = collection.distinct(
            "shape_id",
            {"route_id": route_id}
        )

        return shapes
    except Exception as e:
        print(e)

def get_trips(route_id: str):
    try:
        db: Database = client[MONGO_DATABASE]
        collection: Collection = db["metropolitan_tram_trips"]

        # Get list of all documents, excluding "_id" and "version" field
        documents = list(collection.find({"route_id": route_id}, {"_id": 0, "version": 0}))
        return documents
    except Exception as e:
        print(e)