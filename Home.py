import streamlit as st
import requests
import pandas as pd
from datetime import datetime
import altair as alt
from mongodb import upload_to_mongo, fetch_new_data

st.set_page_config(
    page_title="FaYmuni Dashboard",
    layout="wide"
)

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.username = None

if not st.session_state.logged_in:
    st.switch_page("pages/Login.py")


st.markdown(
    """
    <style>
    /* Ẩn menu và footer mặc định của Streamlit */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}

    /* Tuỳ biến cho cột bên trái */
    .col1-container {
        background-color: #6EA693;
        padding: 20px;
        border-radius: 10px;
        min-height: 80vh;
        color: white;
    }
    .title-faymuni {
        font-size: 1.8rem;
        font-weight: bold;
        margin-bottom: 20px;
    }
    .menu-button {
        margin: 10px 0;
        width: 100%;
        background-color: #4E7B70;
        color: #FFFFFF;
        border: none;
        padding: 10px;
        border-radius: 5px;
        text-align: left;
        font-size: 1rem;
        cursor: pointer;
    }
    .menu-button:hover {
        background-color: #3D6157;
    }

    /* Tuỳ biến cho ô trung tâm */
    .center-box {
        background-color: #AEC9C1;
        border-radius: 10px;
        min-height: 200px;
        margin: 10px;
        padding: 20px;
        text-align: center;
        font-weight: bold;
        font-size: 1.2rem;
    }

    /* Tuỳ biến cho cột bên phải */
    .info-card {
        background-color: #BAE8E491;
        border-radius: 10px;
        padding: 20px;
        margin: 10px 0;
        text-align: center;
        color: #000000;
        font-weight: bold;
        font-size: 1.1rem;
    }
    .info-title {
        font-size: 1.2rem;
        margin-bottom: 5px;
    }
    .info-value {
        font-size: 1.6rem;
        color: #333333;
    }

    .full-width { width: 100%; }
    </style>
    """,
    unsafe_allow_html=True
)

# Lấy toàn bộ dữ liệu từ API

def fetch_data(endpoint):
    url = f"http://127.0.0.1:5000/aio/{endpoint}?limit=all"
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        if not isinstance(data, list):
            st.error(f"Lỗi API {endpoint}: {data}")
            return []
        processed = []
        for x in data:
            dt = datetime.fromisoformat(x['created_at'].replace("Z", "+00:00"))
            processed.append({"datetime": dt, "value": x['value']})
        return processed
    except requests.exceptions.RequestException as e:
        st.error(f"Lỗi API {endpoint}: {e}")
        return []

# Đăng tải dữ liệu mới lên MongoDB

endpoints = {
    "temperature": fetch_data("temperature"),
    "soil_moisture": fetch_data("soil_moisture"),
    "humidity": fetch_data("humidity"),
    "light_intensity": fetch_data("light_intensity"),
    "status": fetch_data("status")
}

# Chuyển status thành tomato
status_data = [x for x in endpoints['status'] if x['value'] in ['Chín', 'Chưa chín']]
col_map = {
    "temperature": "temp",
    "soil_moisture": "mois",
    "humidity": "humid",
    "light_intensity": "light",
    "status": "tomato"
}
# Upload từng feed
for name, data in endpoints.items():
    if name == 'status':
        upload_to_mongo(status_data, "FaYmuni", col_map[name])
    else:
        upload_to_mongo(data, "FaYmuni", col_map[name])

col1, col2, col3 = st.columns([1, 10, 1])

with col1:
    if st.button("Control Panel"): st.switch_page("pages/control_page.py")
    if st.button("Analysis"):      st.switch_page("pages/analysis_page.py")
    if st.button("Out Page"):      st.switch_page("pages/landing_page.py")

with col2:
    top_left, top_right = st.columns(2)
    bottom_left, bottom_right = st.columns(2)

    def plot_chart(time, data, title, ylabel, height=400):
        df = pd.DataFrame({"Time": time, "Value": data})
        chart = (
            alt.Chart(df)
            .mark_line(point=True)
            .encode(x="Time:T", y="Value:Q", tooltip=["Time", "Value"] )
            .properties(title=title, width="container", height=height)
        )
        st.altair_chart(chart, use_container_width=True)

    # Vẽ biểu đồ không lọc
    def draw(feed, title, unit, container):
        data = endpoints[feed]
        if data:
            times = [d["datetime"] for d in data]
            values = [d["value"] for d in data]
            plot_chart(times, values, title, unit)
        else:
            with container: st.warning(f"Không có dữ liệu cho {title}")

    with top_left:    draw("temperature", "Temperature", "°C", top_left)
    with top_right:   draw("soil_moisture", "Soil Moisture", "%", top_right)
    with bottom_left: draw("humidity",    "Humidity",    "%", bottom_left)
    with bottom_right:draw("light_intensity", "Light Intensity", "Lux", bottom_right)

with col3:
    st.markdown(f"<div class='info-card'><div class='info-title'>Temperature</div><div class='info-value'>{endpoints['temperature'][0]['value'] if endpoints['temperature'] else 'N/A'}°C</div></div>", unsafe_allow_html=True)
    st.markdown(f"<div class='info-card'><div class='info-title'>Soil Moisture</div><div class='info-value'>{endpoints['soil_moisture'][0]['value'] if endpoints['soil_moisture'] else 'N/A'}%</div></div>", unsafe_allow_html=True)
    st.markdown(f"<div class='info-card'><div class='info-title'>Humidity</div><div class='info-value'>{endpoints['humidity'][0]['value'] if endpoints['humidity'] else 'N/A'}%</div></div>", unsafe_allow_html=True)
    st.markdown(f"<div class='info-card'><div class='info-title'>Light Intensity</div><div class='info-value'>{endpoints['light_intensity'][0]['value'] if endpoints['light_intensity'] else 'N/A'} Lux</div></div>", unsafe_allow_html=True)
