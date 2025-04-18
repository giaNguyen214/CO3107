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


st.markdown(
    """
    <style>
    /* Ẩn menu và footer mặc định của Streamlit (nếu muốn) */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}

    /* Tuỳ biến cho cột bên trái (col1) */
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

    /* Tuỳ biến cho khu vực trung tâm (col2) - chứa 4 ô vuông */
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

    /* Tuỳ biến cho cột bên phải (col3) - các thẻ thông tin */
    .info-card {
        background-color: #BAE8E491; /* màu nền chung, tuỳ ý thay đổi */
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

    /* Đảm bảo các phần tử hiển thị toàn chiều rộng cột */
    .full-width {
        width: 100%;
    }

    </style>
    """,
    unsafe_allow_html=True
)



def fetch_data(endpoint, limit):
    url = f"http://127.0.0.1:5000/{endpoint}?limit={limit}"
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        # print(data)

        if not isinstance(data, list):
            st.error(f"Lỗi API {endpoint}: {data}")
            return []

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
        st.error(f"Lỗi API {endpoint}: {e}")
        return []



temperature_data = fetch_data("temperature", "all")
soil_moisture_data = fetch_data("soil_moisture", "all")
humidity_data = fetch_data("humidity", "all")
light_intensity_data = fetch_data("light_intensity", "all")


ENDPOINTS = ["temperature", "soil_moisture", "humidity", "light_intensity"]
DATA_MAP = {
    "temperature": temperature_data,
    "soil_moisture": soil_moisture_data,
    "humidity": humidity_data,
    "light_intensity": light_intensity_data
}
feed_collection_map = {
    "temperature": "temp",
    "soil_moisture": "mois",
    "humidity": "humid",
    "light_intensity": "light"
}

for endpoint in ENDPOINTS:
    all_data = DATA_MAP[endpoint]
    new_data = fetch_new_data(endpoint, all_data)
    upload_to_mongo(new_data, "FaYmuni", feed_collection_map[endpoint])



col1, col2, col3 = st.columns([1, 10, 1])


with col1:
    if st.button("Control Panel"):
        st.switch_page("pages/control_page.py")
    if st.button("Analysis"):
        st.switch_page("pages/analysis_page.py")
    if st.button("Out Page"):
        st.switch_page("pages/landing_page.py")


with col2:
    top_left, top_right = st.columns(2)
    bottom_left, bottom_right = st.columns(2)

    def plot_chart(time, data, title, xlabel, ylabel, height=400):
        df = pd.DataFrame({"Time": time, "Value": data})
        df = df.set_index("Time").reset_index()  

        chart = (
            alt.Chart(df)
            .mark_line(point=True)
            .encode(
                x="Time:T", 
                y="Value:Q",
                tooltip=["Time", "Value"]
            )
            .properties(
                title=title,
                width="container",
                height=height
            )
        )

        st.altair_chart(chart, use_container_width=True)



    def filter_data(sensor_data, title):
        df = pd.DataFrame(sensor_data)

        if df.empty:
            st.warning(f"Không có dữ liệu cho {title}")
            return None, None

        selected_year = 2025
        selected_month = st.selectbox(f"Chọn tháng ({title})", sorted(df[df["year"] == selected_year]["month"].unique(), reverse=True))
        selected_day = st.selectbox(f"Chọn ngày ({title})", sorted(df[(df["year"] == selected_year) & (df["month"] == selected_month)]["day"].unique(), reverse=True))

        filtered_df = df[(df["year"] == selected_year) & 
                         (df["month"] == selected_month) & 
                         (df["day"] == selected_day)]

        return filtered_df["datetime"], filtered_df["value"]

    with top_left:
        timestamps, values = filter_data(temperature_data, "Temperature")
        if timestamps is not None:
            plot_chart(timestamps, values, "Temperature", "Time", "°C")

    with top_right:
        timestamps, values = filter_data(soil_moisture_data, "Soil Moisture")
        if timestamps is not None:
            plot_chart(timestamps, values, "Soil Moisture", "Time", "%")

    with bottom_left:
        timestamps, values = filter_data(humidity_data, "Humidity")
        if timestamps is not None:
            plot_chart(timestamps, values, "Humidity", "Time", "%")

    with bottom_right:
        timestamps, values = filter_data(light_intensity_data, "Light Intensity")
        if timestamps is not None:
            plot_chart(timestamps, values, "Light Intensity", "Time", "Lux")

with col3:
    st.markdown(f"<div class='info-card'><div class='info-title'>Temperature</div><div class='info-value'>{temperature_data[0]['value'] if temperature_data else 'N/A'}°C</div></div>", unsafe_allow_html=True)
    st.markdown(f"<div class='info-card'><div class='info-title'>Soil Moisture</div><div class='info-value'>{soil_moisture_data[0]['value'] if soil_moisture_data else 'N/A'}%</div></div>", unsafe_allow_html=True)
    st.markdown(f"<div class='info-card'><div class='info-title'>Humidity</div><div class='info-value'>{humidity_data[0]['value'] if humidity_data else 'N/A'}%</div></div>", unsafe_allow_html=True)
    st.markdown(f"<div class='info-card'><div class='info-title'>Light Intensity</div><div class='info-value'>{light_intensity_data[0]['value'] if light_intensity_data else 'N/A'} Lux</div></div>", unsafe_allow_html=True)
