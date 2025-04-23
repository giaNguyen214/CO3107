import sys
from Adafruit_IO import MQTTClient
import pandas as pd
import requests
from datetime import datetime

GDD_ID = "yolofarm.farm-gdd"
HUMIDITY_ID = "yolofarm.farm-humidity"
LIGHT_INTENSITY_ID = "yolofarm.farm-light-intensity"
PUMP1_ID = "yolofarm.farm-pump1"
PUMP2_ID = "yolofarm.farm-pump2"
SOIL_MOISTURE_ID = "yolofarm.farm-soil-moisture"
STATUS_ID = "yolofarm.farm-status"
TEMPERATURE_ID = "yolofarm.farm-temperature"


from dotenv import load_dotenv
import os
# Load environment variables
dotenv_path = os.getenv('DOTENV_PATH', None)
if dotenv_path:
    load_dotenv(dotenv_path)
else:
    load_dotenv()
    
AIO_USERNAME = os.getenv("AIO_USERNAME")
AIO_KEY = os.getenv("AIO_KEY")

# Global variable to store the latest data
latest_payload = None

# --- Function to fetch soil data ---
def fetch_data(endpoint, limit):
    url = f"http://127.0.0.1:5000/aio/{endpoint}?limit={limit}"
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        processed_data = []
        for x in data:
            dt = datetime.fromisoformat(x['created_at'].replace("Z", "+00:00"))
            processed_data.append({
                "value": x["value"],
                "day": dt.day,
                "month": dt.month,
                "year": dt.year,
                "hour": dt.hour,
                "datetime": dt
            })
        return processed_data
    except requests.exceptions.RequestException as e:
        return []

def connected(client):
    print("Kết nối thành công ...")
    client.subscribe(SOIL_MOISTURE_ID)

def subscribe(client, userdata, mid, granted_qos):
    print("Đã đăng ký thành công ...")

def disconnected(client):
    print("Ngắt kết nối ...")
    sys.exit(1)

def message(client, feed_id, payload):
    global latest_payload
    print("Nhận dữ liệu: " + payload)
    latest_payload = payload  # Cập nhật dữ liệu mới vào biến toàn cục

client = MQTTClient(AIO_USERNAME, AIO_KEY)
client.on_connect = connected
client.on_disconnect = disconnected
client.on_message = message
client.on_subscribe = subscribe
client.connect()
client.loop_background()

def get_latest_moisture():
    # Lấy dữ liệu soil_moisture
    soil_moisture_data = fetch_data("soil_moisture", "all")

    # Lọc ra ngày mới nhất (nếu có)
    days = pd.Series([x["day"] for x in soil_moisture_data]).unique()
    latest_day = max(days) if len(days) > 0 else None

    moisture = None
    if latest_day:
        # Tìm bản ghi có datetime lớn nhất trong ngày đó
        latest_record = max(soil_moisture_data, key=lambda x: x["datetime"])

        # Lấy moisture từ bản ghi đó
        moisture = latest_record.get("value", None)
        # print("latest_record: ", latest_record)
        
    print("moisture: ", moisture)
    if moisture:
        return moisture
    if latest_payload:
        return latest_payload
    return 0
