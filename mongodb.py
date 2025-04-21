import os
import requests
from datetime import datetime, timezone
from pymongo import MongoClient
from dotenv import load_dotenv
load_dotenv()

DATA_FOLDER = "data"

# ─── MongoDB ───────────────────────────────────────────
def upload_to_mongo(data, db_name="faymuni", collection_name="sensor_data"):
    try:
        client = MongoClient(os.getenv("MONGO_URI"))
        db = client[db_name]
        collection = db[collection_name]

        if data:
            result = collection.insert_many(data)
            print(f"Inserted {len(result.inserted_ids)} documents into MongoDB.")
        else:
            print("No new data to insert.")
    except Exception as e:
        print(f"MongoDB Error: {e}")

# File Utility ──────────────────────────────────────
def ensure_data_folder():
    os.makedirs(DATA_FOLDER, exist_ok=True)

def get_last_time_file(endpoint):
    return os.path.join(DATA_FOLDER, f"last_time_{endpoint}.txt")

def load_last_time(endpoint):
    path = get_last_time_file(endpoint)
    if not os.path.exists(path):
        return datetime.fromtimestamp(0, tz=timezone.utc)
    return datetime.fromisoformat(open(path).read().strip())

def save_last_time(endpoint, dt: datetime):
    path = get_last_time_file(endpoint)
    with open(path, "w") as f:
        f.write(dt.isoformat())

# Filter new data  ──────────────────────── 
def fetch_new_data(feed_name: str, all_data: list):
    ensure_data_folder()

    last_time = load_last_time(feed_name)
    new_data = []
    newest = last_time

    for item in all_data:
        if not isinstance(item, dict) or "datetime" not in item:
            continue
        created = item["datetime"]
        if created > last_time:
            new_data.append(item)
            if created > newest:
                newest = created

    if new_data:
        save_last_time(feed_name, newest)
        print(f"[{feed_name}] Added {len(new_data)} new records up to {newest.isoformat()}")
    else:
        print(f"[{feed_name}] No new data found.")

    return new_data
