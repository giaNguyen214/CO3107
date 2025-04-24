import os
import requests
from flask import Flask, jsonify, request
from pymongo import MongoClient
from datetime import datetime, timezone, timedelta
from bson import ObjectId
from dotenv import load_dotenv
import pytz  # Sử dụng thư viện pytz để xử lý múi giờ chính xác

# Load environment variables
dotenv_path = os.getenv('DOTENV_PATH', None)
if dotenv_path:
    load_dotenv(dotenv_path)
else:
    load_dotenv()

# Initialize Flask app and MongoDB client
app = Flask(__name__)

# ---------------------
# AIO CONFIGURATION
# ---------------------
AIO_USERNAME = os.getenv("AIO_USERNAME")
AIO_KEY = os.getenv("AIO_KEY")

GDD_ID = "yolofarm.farm-gdd"
HUMIDITY_ID = "yolofarm.farm-humidity"
LIGHT_INTENSITY_ID = "yolofarm.farm-light-intensity"
PUMP1_ID = "yolofarm.farm-pump1"
PUMP2_ID = "yolofarm.farm-pump2"
SOIL_MOISTURE_ID = "yolofarm.farm-soil-moisture"
STATUS_ID = "yolofarm.farm-status"
TEMPERATURE_ID = "yolofarm.farm-temperature"

# ---------------------
# MONGO CONFIGURATION
# ---------------------
MONGO_URI = os.getenv("MONGO_URI")
DATA_FOLDER = os.getenv("DATA_FOLDER", "data")
client = MongoClient(MONGO_URI)
db = client[os.getenv("MONGO_DB_NAME", "FaYmuni")]

humid_col      = db[os.getenv("HUMID_COLLECTION", "humid")]
light_col      = db[os.getenv("LIGHT_COLLECTION", "light")]
mois_col       = db[os.getenv("MOIS_COLLECTION", "mois")]
temp_col       = db[os.getenv("TEMP_COLLECTION", "temp")]
scheduler_col  = db[os.getenv("SCHEDULER_COLLECTION", "watering_scheduler")]
user_col = db[os.getenv("USER_COLLECTION", "user")]
auto_watering_col = db[os.getenv("AUTO_WATERING_COLLECTION", "auto_watering")]


# ---------------------
# AIO DATA FETCHER
# ---------------------
def fetch_aio_data(feed_id, feed_name):
    limit = request.args.get("limit") 
    url = f"https://io.adafruit.com/api/v2/{AIO_USERNAME}/feeds/{feed_id}/data"

    if limit and str(limit).lower() != "all":  
        url += f"?limit={limit}"

    headers = {"X-AIO-Key": AIO_KEY}
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        data = response.json()
        for item in data:
            if "created_at" in item:
                dt_utc = datetime.fromisoformat(item["created_at"].replace("Z", "+00:00")).replace(tzinfo=timezone.utc)
                dt_local = dt_utc.astimezone()
                item["created_at_local"] = dt_local.strftime("%Y-%m-%d %H:%M:%S")  
        return jsonify(data)

    return jsonify({"error": f"Error getting {feed_name} data", "status": response.status_code})

# ---------------------
# AIO ROUTES
# ---------------------
@app.route("/aio/light_intensity", methods=["GET"])
def get_light_intensity(): return fetch_aio_data(LIGHT_INTENSITY_ID, "light intensity")

@app.route("/aio/pump1", methods=["GET"])
def get_pump1(): return fetch_aio_data(PUMP1_ID, "pump1")

@app.route("/aio/pump2", methods=["GET"])
def get_pump2(): return fetch_aio_data(PUMP2_ID, "pump2")

@app.route("/aio/soil_moisture", methods=["GET"])
def get_soil_moisture(): return fetch_aio_data(SOIL_MOISTURE_ID, "soil moisture")

@app.route("/aio/status", methods=["GET"])
def get_status(): return fetch_aio_data(STATUS_ID, "status")

@app.route("/aio/temperature", methods=["GET"])
def get_temperature_aio(): return fetch_aio_data(TEMPERATURE_ID, "temperature")

@app.route("/aio/humidity", methods=["GET"])
def get_humidity_aio(): return fetch_aio_data(HUMIDITY_ID, "humidity")

# ---------------------
# MONGO UTILITIES
# ---------------------
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
        "minute":      doc.get("minute"),
        "datetime":    doc.get("datetime"),
        "datetime_local": dt_local.strftime("%Y-%m-%d %H:%M:%S") if dt_local else None
    }

def fetch_data(collection, feed_name):
    limit = request.args.get("limit")
    try:
        cursor = collection.find().sort("datetime", -1)
        if limit and str(limit).lower() != "all":
            cursor = cursor.limit(int(limit))
        return jsonify([format_doc(doc) for doc in cursor])
    except Exception as e:
        return jsonify({"error": f"Error fetching {feed_name} data", "details": str(e)}), 500

# ---------------------
# MONGO ROUTES
# ---------------------
@app.route("/mongo/humidity", methods=["GET"])
def get_humidity(): return fetch_data(humid_col, "humidity")

@app.route("/mongo/light", methods=["GET"])
def get_light(): return fetch_data(light_col, "light")

@app.route("/mongo/moisture", methods=["GET"])
def get_moisture(): return fetch_data(mois_col, "moisture")

@app.route("/mongo/temperature", methods=["GET"])
def get_temperature(): return fetch_data(temp_col, "temperature")

@app.route("/users", methods=["GET"])
def get_users():
    try:
        # Lấy toàn bộ users, chỉ select username và password
        cursor = user_col.find({}, {"_id": 0, "username": 1, "password": 1})
        users = list(cursor)
        return jsonify(users)
    except Exception as e:
        return jsonify({"error": "Error fetching users", "details": str(e)}), 500

@app.route("/auto-watering", methods=["GET"])
def get_auto_watering():
    try:
        cursor = auto_watering_col.find().sort("datetime", -1)
        return jsonify([format_doc(doc) for doc in cursor])
    except Exception as e:
        return jsonify({"error": "Error fetching auto-watering data", "details": str(e)}), 500

@app.route("/auto-watering", methods=["POST"])
def create_auto_watering():
    data = request.json or {}

    # Kiểm tra các trường bắt buộc
    for field in ("day", "month", "year", "hour", "minute"):
        if field not in data:
            return jsonify({"error": f"Missing field: {field}"}), 400

    # Dựng datetime từ giờ địa phương (GMT+7)
    try:
        # Giả sử giờ gửi từ client là theo múi giờ địa phương GMT+7
        local_timezone = pytz.timezone("Asia/Ho_Chi_Minh")  # Múi giờ Việt Nam
        dt_local = datetime(
            year=int(data["year"]), month=int(data["month"]),
            day=int(data["day"]), hour=int(data["hour"]),
            minute=int(data["minute"])
        )

        # Đặt múi giờ cho datetime là GMT+7
        dt_local = local_timezone.localize(dt_local)

        # Lấy giờ theo GMT+7
        dt_hour_gmt7 = dt_local.strftime("%H")  # Giờ đúng theo múi giờ GMT+7

        # Chuyển datetime sang UTC nếu cần (để lưu vào cơ sở dữ liệu)
        dt_utc = dt_local.astimezone(pytz.utc)
    except ValueError as e:
        return jsonify({"error": "Invalid date/time", "details": str(e)}), 400

    # Kiểm tra trùng
    if auto_watering_col.find_one({"datetime": dt_utc.isoformat()}):
        return jsonify({"error": "Auto-watering schedule already exists at this datetime"}), 400

    new_doc = {
        "day": dt_local.day, "month": dt_local.month,
        "year": dt_local.year, "hour": dt_hour_gmt7,  # Lưu giờ theo GMT+7
        "minute": dt_local.minute, "datetime": dt_utc.isoformat()
    }

    result = auto_watering_col.insert_one(new_doc)
    return jsonify({"message": "Auto-watering schedule created", "id": str(result.inserted_id)})

# ---------------------
# SCHEDULE CRUD
# ---------------------
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
    # chỉ kiểm tra 4 trường cơ bản
    for field in ("day","month","year","hour","minute"):
        if field not in data:
            return jsonify({"error": f"Missing field: {field}"}), 400

    # dựng datetime UTC (hoặc timezone bạn muốn)
    try:
        dt = datetime(
            year=int(data["year"]), month=int(data["month"]),
            day=int(data["day"]), hour=int(data["hour"]),
            minute=int(data["minute"]),
            tzinfo=timezone.utc
        )
    except ValueError as e:
        return jsonify({"error": "Invalid date/time", "details": str(e)}), 400

    # kiểm tra không phải lịch quá khứ
    if dt < datetime.now(timezone.utc):
        return jsonify({"error": "Cannot schedule in the past"}), 400

    # kiểm tra trùng
    if scheduler_col.find_one({"datetime": dt.isoformat()}):
        return jsonify({"error": "Schedule at this datetime already exists"}), 400

    # lưu vào DB với datetime đã dựng
    new_doc = {
        "day": dt.day,
        "month": dt.month,
        "year": dt.year,
        "hour": dt.hour,
        "minute": dt.minute,
        "datetime": dt.isoformat()
    }
    result = scheduler_col.insert_one(new_doc)
    return jsonify({"message": "Schedule created", "id": str(result.inserted_id)})

@app.route("/schedule/<id>", methods=["PUT"])
def update_schedule(id):
    data = request.json or {}
    for field in ("day","month","year","hour","minute"):
        if field not in data:
            return jsonify({"error": f"Missing field: {field}"}), 400

    # dựng lại dt mới
    dt = datetime(
        year=int(data["year"]), month=int(data["month"]),
        day=int(data["day"]), hour=int(data["hour"]),
        minute=int(data["minute"]),
        tzinfo=timezone.utc
    )
    # kiểm tra trùng (ngoại trừ chính bản ghi này)
    existing = scheduler_col.find_one({
        "datetime": dt.isoformat(),
        "_id": {"$ne": ObjectId(id)}
    })
    if existing:
        return jsonify({"error": "Another schedule already exists at this datetime"}), 400

    update_doc = {
        "day": dt.day, "month": dt.month,
        "year": dt.year, "hour": dt.hour,
        "minute": dt.minute,
        "datetime": dt.isoformat()
    }
    result = scheduler_col.update_one(
        {"_id": ObjectId(id)},
        {"$set": update_doc}
    )
    return jsonify({"message": result.modified_count and "Schedule updated" or "No changes made"})


@app.route("/schedule/<id>", methods=["DELETE"])
def delete_schedule(id):
    result = scheduler_col.delete_one({"_id": ObjectId(id)})
    return jsonify({"message": "Schedule deleted"} if result.deleted_count else {"message": "Schedule not found"})

# ---------------------
# RUN
# ---------------------
if __name__ == "__main__":
    app.run(debug=True, port=int(os.getenv("PORT", 5000)))
