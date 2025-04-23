import streamlit as st
import requests
from datetime import datetime, date, time as dt_time
import os
from mqtt_server import get_latest_moisture
from pymongo import MongoClient
import threading
import sys
import time  # module for sleep

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# --- Page config (phải đứng trước các gọi st khác) ---
st.set_page_config(page_title="Watering Dashboard", layout="wide")

# --- Khởi tạo mọi khóa trong session_state ---
for key, default in [
    ('running', True),
    ('moisture', None),
    ('update_flag', False),
    ('edit_id', None),
    ('edit_date', date.today()),
    ('edit_time', dt_time(datetime.now().hour, datetime.now().minute)),
    ('thread_started', False),
    ('logged_in', False),
    ('adding_schedule', False)
]:
    if key not in st.session_state:
        st.session_state[key] = default

# --- Kiểm tra login ---
if not st.session_state.get('logged_in', False):
    st.switch_page("pages/Login.py")

# --- CSS custom ---
st.markdown("""
<style>
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
body {
    background-color: #F0F0F0;
    font-family: "Arial", sans-serif;
}
</style>
""", unsafe_allow_html=True)

# --- MongoDB setup ---
client = MongoClient(
    "mongodb+srv://bach:krSHyYi28-nib5a@cluster0.q27psbu.mongodb.net/"
    "?retryWrites=true&w=majority&appName=Cluster0"
)
db = client['watering_db']
collection = db['watering_log']
BASE_URL = "http://localhost:5000"  # sửa nếu cần

# --- Background thread to fetch moisture ---
def check_moisture():
    while st.session_state.running:
        latest = get_latest_moisture()
        if latest is not None and latest != st.session_state.moisture:
            st.session_state.moisture = latest
            st.session_state.update_flag = True
        time.sleep(5)

from streamlit.runtime.scriptrunner import add_script_run_ctx
if not st.session_state.thread_started:
    t = threading.Thread(target=check_moisture, daemon=True)
    add_script_run_ctx(t)
    t.start()
    st.session_state.thread_started = True

# --- UI Layout ---
col1, col2, col3 = st.columns([1.2, 1.5, 1.5])

# Column 1: Moisture & History
with col1:
    st.markdown("### Current soil moisture:")
    if st.session_state.moisture is not None:
        prog = float(st.session_state.moisture)
        st.markdown(f"**{prog}%**")
        st.progress(prog / 100)
    else:
        st.info("Waiting for sensor data...")

    st.markdown("#### Watering History")
    for wh in ["1/20 10:00 to 11:00","1/21 08:00 to 09:00","1/23 16:00 to 17:00",
               "1/24 09:30 to 10:00","1/25 10:00 to 10:30"]:
        st.markdown(f"- {wh}")

    if st.button("Dashboard"):
        st.switch_page("./main.py")

# Column 2: Schedule
with col2:
    st.markdown("### Watering Schedule")

    # API helpers
    def fetch_schedules():
        try:
            r = requests.get(f"{BASE_URL}/schedule")
            return r.json() if r.ok else []
        except:
            return []

    def add_schedule(d, t):
        payload = {"day":d.day,"month":d.month,"year":d.year,
                   "hour":t.hour,"minute":t.minute}
        try:
            r = requests.post(f"{BASE_URL}/schedule", json=payload)
            if r.ok: st.success("Schedule created.")
            else:    st.error(r.json().get("error","Unknown"))
        except Exception as e:
            st.error(f"Request failed: {e}")
        finally:
            st.session_state.update_flag = True

    def update_schedule(sid, d, t):
        payload = {"day":d.day,"month":d.month,"year":d.year,
                   "hour":t.hour,"minute":t.minute}
        try:
            r = requests.put(f"{BASE_URL}/schedule/{sid}", json=payload)
            if r.ok: st.success("Schedule updated.")
            else:    st.error(r.json().get("error","Unknown"))
        except Exception as e:
            st.error(f"Request failed: {e}")
        finally:
            st.session_state.update_flag = True

    def delete_schedule(sid):
        try:
            requests.delete(f"{BASE_URL}/schedule/{sid}")
        except:
            pass
        # reset edit state
        for k in ("edit_id", "edit_date", "edit_time"):
            st.session_state.pop(k, None)
        st.session_state.update_flag = True
        st.rerun()  # 🛠️ Trigger rerun ngay lập tức sau khi xóa


    # Render list
    schedules = fetch_schedules()
    for item in schedules:
        c1, c2, c3 = st.columns([5,1,1])
        with c1:
            hr = item.get("hour")  or 0
            mi = item.get("minute") or 0
            st.markdown(f"**{item['day']:02}/{item['month']:02} ({hr:02}:{mi:02})**")
        with c2:
            if st.button("✏️", key=f"edit_{item['id']}"):
                st.session_state.edit_id   = item['id']
                st.session_state.edit_date = date(item["year"],item["month"],item["day"])
                st.session_state.edit_time = dt_time(hr,mi)
        with c3:
            if st.button("🗑️", key=f"del_{item['id']}"):
                delete_schedule(item['id'])

    if st.button("➕ Add Schedule"):
        st.session_state.adding_schedule = True

    edit_mode = st.session_state.edit_id is not None
    adding_mode = st.session_state.adding_schedule

    if edit_mode or adding_mode:
        st.markdown("#### Add or Edit Schedule")
        with st.form("schedule_form"):
            default_d = st.session_state.get("edit_date", date.today())
            default_t = st.session_state.get("edit_time", dt_time(datetime.now().hour, datetime.now().minute))

            d_in = st.date_input("Select Date", value=default_d)
            t_in = st.time_input("Select Time", value=default_t)

            if edit_mode:
                submitted = st.form_submit_button("💾 Save Changes")
                if submitted:
                    update_schedule(st.session_state.edit_id, d_in, t_in)
                    st.session_state.pop("edit_id", None)
                    st.session_state.update_flag = True
                    st.rerun()
            else:
                submitted = st.form_submit_button("✅ Add Schedule")
                if submitted:
                    add_schedule(d_in, t_in)
                    st.session_state.adding_schedule = False
                    st.rerun()


# Column 3: Auto Watering
with col3:
    threshold = st.slider("Set moisture threshold", 0, 100, 30)
    st.markdown(f"Threshold: **{threshold}%**")
    if (st.session_state.moisture is not None
        and float(st.session_state.moisture) < threshold):
        st.warning("Soil below threshold, auto-watering...")
        collection.insert_one({
            "moisture":st.session_state.moisture,
            "action":"Auto watering",
            "timestamp":datetime.now()
        })
        st.success("Watering logged.")

# --- Single rerun trigger ---
while True:
    if st.session_state.update_flag:
        st.session_state.update_flag = False
        st.rerun()
