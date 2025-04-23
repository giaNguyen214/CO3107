import os
import requests
from flask import Flask, jsonify, request
from pymongo import MongoClient
from datetime import datetime, timezone, timedelta
from bson import ObjectId
from dotenv import load_dotenv

# Load environment variables
dotenv_path = os.getenv('DOTENV_PATH', None)
if dotenv_path:
    load_dotenv(dotenv_path)
else:
    load_dotenv()

# Configuration
MONGO_URI = os.getenv("MONGO_URI", "mongodb+srv://bach:krSHyYi28-nib5a@cluster0.q27psbu.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")
DATA_FOLDER = os.getenv("DATA_FOLDER", "data")

# Initialize Flask app and MongoDB client
app = Flask(__name__)
client = MongoClient(MONGO_URI)
db = client[os.getenv("MONGO_DB_NAME", "FaYmuni")]

# Collections
humid_col      = db[os.getenv("HUMID_COLLECTION", "humid")]
light_col      = db[os.getenv("LIGHT_COLLECTION", "light")]
mois_col       = db[os.getenv("MOIS_COLLECTION", "mois")]
temp_col       = db[os.getenv("TEMP_COLLECTION", "temp")]
scheduler_col  = db[os.getenv("SCHEDULER_COLLECTION", "watering_scheduler")]

# --------------------
# Data Formatting
# --------------------
def format_doc(doc):
    dt_local = None
    try:
        dt = datetime.fromisoformat(doc.get("datetime").replace("Z", "+00:00"))
        dt_local = dt.astimezone(timezone(timedelta(hours=7)))
    except Exception:
        pass

    return {
        "id":          str(doc.get("_id")),
        "value":       doc.get("value"),
        "day":         doc.get("day"),
        "month":       doc.get("month"),
        "year":        doc.get("year"),
        "hour":        doc.get("hour"),
        "datetime":    doc.get("datetime"),
        "datetime_local": dt_local.strftime("%Y-%m-%d %H:%M:%S") if dt_local else None
    }

# --------------------
# Generic Fetcher
# --------------------
def fetch_data(collection, feed_name):
    limit = request.args.get("limit")
    try:
        cursor = collection.find().sort("datetime", -1)
        if limit and str(limit).lower() != "all":
            cursor = cursor.limit(int(limit))
        return jsonify([format_doc(doc) for doc in cursor])
    except Exception as e:
        return jsonify({"error": f"Error fetching {feed_name} data", "details": str(e)}), 500

# === GET endpoints for sensor feeds ===
@app.route("/humidity",   methods=["GET"])
def get_humidity():    return fetch_data(humid_col, "humidity")

@app.route("/light",      methods=["GET"])
def get_light():       return fetch_data(light_col, "light")

@app.route("/moisture",   methods=["GET"])
def get_moisture():    return fetch_data(mois_col, "moisture")

@app.route("/temperature",methods=["GET"])
def get_temperature(): return fetch_data(temp_col, "temperature")

# --------------------
# Scheduler CRUD
# --------------------

def is_duplicate_schedule(dt_iso):
    return scheduler_col.find_one({"datetime": dt_iso}) is not None


def is_valid_datetime(dt_iso):
    try:
        dt = datetime.fromisoformat(dt_iso)
        return dt >= datetime.now(timezone.utc)
    except ValueError:
        return False

@app.route("/schedule", methods=["GET"])
def get_schedules():
    cursor = scheduler_col.find().sort("datetime", -1)
    return jsonify([format_doc(doc) for doc in cursor])

@app.route("/schedule", methods=["POST"])
def create_schedule():
    data = request.json or {}
    # Validate required fields
    for field in ("day","month","year","hour","datetime"): 
        if field not in data:
            return jsonify({"error": f"Missing field: {field}"}), 400

    dt_iso = data["datetime"]
    if not is_valid_datetime(dt_iso):
        return jsonify({"error": "Invalid or past datetime"}), 400
    if is_duplicate_schedule(dt_iso):
        return jsonify({"error": "Schedule at this datetime already exists"}), 400

    new_doc = {k: data[k] for k in ("day","month","year","hour","datetime")}
    result = scheduler_col.insert_one(new_doc)
    return jsonify({"message": "Schedule created", "id": str(result.inserted_id)})

@app.route("/schedule/<id>", methods=["PUT"])
def update_schedule(id):
    data = request.json or {}
    dt_iso = data.get("datetime")
    if not dt_iso or not is_valid_datetime(dt_iso):
        return jsonify({"error": "Invalid or missing datetime"}), 400

    # Check for duplicates except self
    existing = scheduler_col.find_one({"datetime": dt_iso, "_id": {"$ne": ObjectId(id)}})
    if existing:
        return jsonify({"error": "Another schedule already exists at this datetime"}), 400

    update_doc = {k: data.get(k) for k in ("day","month","year","hour","datetime")}
    result = scheduler_col.update_one({"_id": ObjectId(id)}, {"$set": update_doc})
    return jsonify({"message": "Schedule updated"} if result.modified_count else {"message": "No changes made"})

@app.route("/schedule/<id>", methods=["DELETE"])
def delete_schedule(id):
    result = scheduler_col.delete_one({"_id": ObjectId(id)})
    return jsonify({"message": "Schedule deleted"} if result.deleted_count else {"message": "Schedule not found"})

# --------------------
# Utilities for data ingestion
# --------------------
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


def fetch_new_data(feed_name: str, all_data: list):
    ensure_data_folder()
    last_time = load_last_time(feed_name)
    new_data = []
    newest = last_time

    for item in all_data:
        if not isinstance(item, dict) or "datetime" not in item:
            continue
        created = datetime.fromisoformat(item["datetime"]
                                        .replace("Z","+00:00"))
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


def upload_to_mongo(data, db_name=None, collection_name=None):
    db_name = db_name or os.getenv("MONGO_DB_NAME", "faymuni");
    collection_name = collection_name or os.getenv("UPLOAD_COLLECTION", "sensor_data");
    try:
        up_client = MongoClient(MONGO_URI)
        up_db = up_client[db_name]
        up_col = up_db[collection_name]
        if data:
            result = up_col.insert_many(data)
            print(f"Inserted {len(result.inserted_ids)} documents into {db_name}.{collection_name}.")
        else:
            print("No new data to insert.")
    except Exception as e:
        print(f"MongoDB Error: {e}")

# Example: standalone script usage
if __name__ == "__main__":
    # Start Flask server
    app.run(debug=True, port=int(os.getenv("PORT", 5001)))
