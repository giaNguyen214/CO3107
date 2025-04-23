from flask import Flask, jsonify, request
from pymongo import MongoClient
from datetime import datetime, timezone
from bson import ObjectId
from datetime import timedelta, timezone
app = Flask(__name__)

# MongoDB Connection
MONGO_URI = "mongodb+srv://bach:krSHyYi28-nib5a@cluster0.q27psbu.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
client = MongoClient(MONGO_URI)
db = client["FaYmuni"]

# Collections
humid_col = db["humid"]
light_col = db["light"]
mois_col = db["mois"]
temp_col = db["temp"]
scheduler_col = db["watering_scheduler"]

# Helper function to format documents
def format_doc(doc):
    dt = None
    try:
        dt = datetime.fromisoformat(doc["datetime"].replace("Z", "+00:00")).astimezone(timezone(timedelta(hours=7)))

    except:
        pass

    return {
        "id": str(doc.get("_id")),
        "value": doc.get("value"),
        "day": doc.get("day"),
        "month": doc.get("month"),
        "year": doc.get("year"),
        "hour": doc.get("hour"),
        "datetime": doc.get("datetime"),
        "datetime_local": dt.strftime("%Y-%m-%d %H:%M:%S") if dt else None
    }

# Generic data fetcher
def fetch_data(collection, feed_name):
    limit = request.args.get("limit")
    try:
        cursor = collection.find().sort("datetime", -1)
        if limit and str(limit).lower() != "all":
            cursor = cursor.limit(int(limit))
        return jsonify([format_doc(doc) for doc in cursor])
    except Exception as e:
        return jsonify({"error": f"Error fetching {feed_name} data", "details": str(e)}), 500

# === GET Endpoints ===
@app.route("/humidity", methods=["GET"])
def get_humidity():
    return fetch_data(humid_col, "humidity")

@app.route("/light", methods=["GET"])
def get_light():
    return fetch_data(light_col, "light")

@app.route("/moisture", methods=["GET"])
def get_moisture():
    return fetch_data(mois_col, "moisture")

@app.route("/temperature", methods=["GET"])
def get_temperature():
    return fetch_data(temp_col, "temperature")

# === CRUD for watering_scheduler ===

# # GET all schedule entries
# @app.route("/schedule", methods=["GET"])
# def get_schedules():
#     cursor = scheduler_col.find().sort("datetime", -1)
#     return jsonify([format_doc(doc) for doc in cursor])

# # POST create new schedule
# @app.route("/schedule", methods=["POST"])
# def create_schedule():
#     data = request.json
#     try:
#         new_doc = {
#             "day": data["day"],
#             "month": data["month"],
#             "year": data["year"],
#             "hour": data["hour"],
#             "datetime": data["datetime"]
#         }
#         result = scheduler_col.insert_one(new_doc)
#         return jsonify({"message": "Schedule created", "id": str(result.inserted_id)})
#     except Exception as e:
#         return jsonify({"error": "Failed to create schedule", "details": str(e)}), 400

# # PUT update schedule by id
# @app.route("/schedule/<id>", methods=["PUT"])
# def update_schedule(id):
#     data = request.json
#     try:
#         update_doc = {
#             "day": data.get("day"),
#             "month": data.get("month"),
#             "year": data.get("year"),
#             "hour": data.get("hour"),
#             "datetime": data.get("datetime")
#         }
#         result = scheduler_col.update_one({"_id": ObjectId(id)}, {"$set": update_doc})
#         if result.modified_count:
#             return jsonify({"message": "Schedule updated"})
#         else:
#             return jsonify({"message": "No changes made"})
#     except Exception as e:
#         return jsonify({"error": "Failed to update schedule", "details": str(e)}), 400

# # DELETE schedule by id
# @app.route("/schedule/<id>", methods=["DELETE"])
# def delete_schedule(id):
#     try:
#         result = scheduler_col.delete_one({"_id": ObjectId(id)})
#         if result.deleted_count:
#             return jsonify({"message": "Schedule deleted"})
#         else:
#             return jsonify({"message": "Schedule not found"})
#     except Exception as e:
#         return jsonify({"error": "Failed to delete schedule", "details": str(e)}), 400



# Helper: Kiểm tra trùng thời gian
def is_duplicate_schedule(dt_iso):
    existing = scheduler_col.find_one({"datetime": dt_iso})
    return existing is not None

# Helper: Kiểm tra ngày giờ có hợp lệ không
def is_valid_datetime(dt_iso):
    try:
        dt = datetime.fromisoformat(dt_iso)
        return dt >= datetime.now()  # Không cho phép tạo lịch trong quá khứ
    except ValueError:
        return False

# GET all schedule entries
@app.route("/schedule", methods=["GET"])
def get_schedules():
    cursor = scheduler_col.find().sort("datetime", -1)
    return jsonify([format_doc(doc) for doc in cursor])

# POST create new schedule
@app.route("/schedule", methods=["POST"])
def create_schedule():
    data = request.json
    try:
        # Kiểm tra trường bắt buộc
        for field in ["day", "month", "year", "hour", "datetime"]:
            if field not in data:
                return jsonify({"error": f"Missing field: {field}"}), 400

        dt_iso = data["datetime"]

        if not is_valid_datetime(dt_iso):
            return jsonify({"error": "Invalid or past datetime"}), 400

        if is_duplicate_schedule(dt_iso):
            return jsonify({"error": "Schedule at this datetime already exists"}), 400

        new_doc = {
            "day": data["day"],
            "month": data["month"],
            "year": data["year"],
            "hour": data["hour"],
            "datetime": dt_iso
        }
        result = scheduler_col.insert_one(new_doc)
        return jsonify({"message": "Schedule created", "id": str(result.inserted_id)})

    except Exception as e:
        return jsonify({"error": "Failed to create schedule", "details": str(e)}), 400


# PUT update schedule by id
@app.route("/schedule/<id>", methods=["PUT"])
def update_schedule(id):
    data = request.json
    try:
        dt_iso = data.get("datetime")

        if not dt_iso or not is_valid_datetime(dt_iso):
            return jsonify({"error": "Invalid or missing datetime"}), 400

        # Kiểm tra xem datetime mới có trùng với lịch đã có không (trừ chính nó)
        existing = scheduler_col.find_one({"datetime": dt_iso, "_id": {"$ne": ObjectId(id)}})
        if existing:
            return jsonify({"error": "Another schedule already exists at this datetime"}), 400

        update_doc = {
            "day": data.get("day"),
            "month": data.get("month"),
            "year": data.get("year"),
            "hour": data.get("hour"),
            "datetime": dt_iso
        }
        result = scheduler_col.update_one({"_id": ObjectId(id)}, {"$set": update_doc})
        if result.modified_count:
            return jsonify({"message": "Schedule updated"})
        else:
            return jsonify({"message": "No changes made"})

    except Exception as e:
        return jsonify({"error": "Failed to update schedule", "details": str(e)}), 400

# DELETE schedule by id
@app.route("/schedule/<id>", methods=["DELETE"])
def delete_schedule(id):
    try:
        result = scheduler_col.delete_one({"_id": ObjectId(id)})
        if result.deleted_count:
            return jsonify({"message": "Schedule deleted"})
        else:
            return jsonify({"message": "Schedule not found"})
    except Exception as e:
        return jsonify({"error": "Failed to delete schedule", "details": str(e)}), 400

# === Run server ===
if __name__ == "__main__":
    app.run(debug=True, port=5001)
