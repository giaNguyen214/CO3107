import os
import json
import requests
from datetime import datetime, timezone

FLASK_BASE = os.getenv("FLASK_BASE", "http://127.0.0.1:5000")
ENDPOINTS = ["temperature", "soil_moisture", "humidity", "light_intensity"]

DATA_FOLDER = "data"

# ─── Helper ────────────────────────────────────────────
def ensure_data_folder():
    os.makedirs(DATA_FOLDER, exist_ok=True)

def get_cache_file(endpoint):
    return os.path.join(DATA_FOLDER, f"data_{endpoint}.json")

def get_last_time_file(endpoint):
    return os.path.join(DATA_FOLDER, f"last_time_{endpoint}.txt")

# ─── Cache Loading ─────────────────────────────────────
def load_cache(endpoint):
    path = get_cache_file(endpoint)
    if not os.path.exists(path):
        return []
    return json.load(open(path))

def save_cache(endpoint, data):
    path = get_cache_file(endpoint)
    with open(path, "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

# ─── Last Time Per Feed ───────────────────────────────
def load_last_time(endpoint):
    path = get_last_time_file(endpoint)
    if not os.path.exists(path):
        return datetime.fromtimestamp(0, tz=timezone.utc)
    txt = open(path).read().strip()
    return datetime.fromisoformat(txt)

def save_last_time(endpoint, dt: datetime):
    path = get_last_time_file(endpoint)
    with open(path, "w") as f:
        f.write(dt.isoformat())

# ─── Adafruit API Call ────────────────────────────────
def fetch_feed(name: str):
    url = f"{FLASK_BASE}/{name}?limit=all"
    resp = requests.get(url, timeout=10)
    resp.raise_for_status()
    return resp.json()

def parse_iso(dt_str: str):
    return datetime.fromisoformat(dt_str.replace("Z", "+00:00"))

# ─── Main Logic ───────────────────────────────────────
def main():
    ensure_data_folder()

    for ep in ENDPOINTS:
        raw = fetch_feed(ep)
        print(f"[DEBUG] {ep} trả về kiểu: {type(raw)}, số lượng: {len(raw) if hasattr(raw, '__len__') else 'N/A'}")
        print(f"[DEBUG] Dòng đầu tiên: {raw[0] if isinstance(raw, list) else raw}")

        cache = load_cache(ep)
        last_time = load_last_time(ep)
        new_data = []
        newest = last_time

        for item in raw:
            if not isinstance(item, dict) or "created_at" not in item:
                continue
            created = parse_iso(item["created_at"])
            if created > last_time:
                item["_feed"] = ep
                new_data.append(item)
                if created > newest:
                    newest = created

        if new_data:
            cache.extend(new_data)
            save_cache(ep, cache)
            save_last_time(ep, newest)
            print(f"[{ep}] ✅ Thêm {len(new_data)} bản ghi mới đến {newest.isoformat()}")
        else:
            print(f"[{ep}] ⏳ Không có dữ liệu mới")

if __name__ == "__main__":
    main()
