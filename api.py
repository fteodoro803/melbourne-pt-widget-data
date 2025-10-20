# import sys
# from typing import Union
# from fastapi import FastAPI
# from pydantic import BaseModel
#
# import pandas as pd
# import json
# import sqlite3
#
# app = FastAPI()
#
#
# class Item(BaseModel):
#     name: str
#     price: float
#     is_offer: Union[bool, None] = None
#
#
# @app.get("/")
# def read_root():
#     return {"Hello": "World!!!"}
#
# @app.get("/tramRoutes")
# async def tramRoutes():
#     db = sqlite3.connect("gtfs.sqlite")
#     query = "SELECT * FROM metropolitan_tram_routes"
#     df = pd.read_sql_query(query, db)
#     db.close()
#
#     # Convert DataFrame to JSON list of dicts
#     data = json.loads(df.to_json(orient="records"))
#
#     return data
#
# @app.get("/tramTrips/{trip_headsign}")
# async def tramTrips(trip_headsign: str):
#     db = sqlite3.connect("gtfs.sqlite")
#     query = "SELECT * FROM metropolitan_train_trips"
#     df = pd.read_sql_query(query, db)
#     filteredDf = df[df["trip_headsign"].str.lower() == trip_headsign.lower()]
#     db.close()
#
#     data = json.loads(filteredDf.to_json(orient="records"))     # Convert DataFrame to JSON list of dicts
#     json_bytes = len(json.dumps(data).encode('utf-8'))
#     print("Approx size of response in bytes:", json_bytes)
#     return data