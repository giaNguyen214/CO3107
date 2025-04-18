from flask import Flask, jsonify, request
import requests
from datetime import datetime, timezone
from dotenv import load_dotenv
import os
load_dotenv()

app = Flask(__name__)


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

# đang lấy có 100 cái đầu thôi
def fetch_data(feed_id, feed_name):
    """Hàm lấy dữ liệu từ Adafruit IO."""
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
                dt_local = dt_utc.astimezone()  # Chuyển về múi giờ địa phương
                item["created_at_local"] = dt_local.strftime("%Y-%m-%d %H:%M:%S")  

        return jsonify(data)

    return jsonify({"error": f"Error getting {feed_name} data", "status": response.status_code})


@app.route("/light_intensity", methods=["GET"])
def get_light_intensity():
    return fetch_data(LIGHT_INTENSITY_ID, "light intensity")

@app.route("/pump1", methods=["GET"])
def get_pump1():
    return fetch_data(PUMP1_ID, "pump1")

@app.route("/pump2", methods=["GET"])
def get_pump2():
    return fetch_data(PUMP2_ID, "pump2")

@app.route("/soil_moisture", methods=["GET"])
def get_soil_moisture():
    return fetch_data(SOIL_MOISTURE_ID, "soil moisture")

@app.route("/status", methods=["GET"])
def get_status():
    return fetch_data(STATUS_ID, "status")

@app.route("/temperature", methods=["GET"])
def get_temperature():
    return fetch_data(TEMPERATURE_ID, "temperature")

@app.route("/humidity", methods=["GET"])
def get_humidity():
    return fetch_data(HUMIDITY_ID, "humidity")

if __name__ == "__main__":
    app.run(debug=True)
