import os
import uuid
import subprocess
from datetime import datetime

import streamlit as st
import pandas as pd
from ultralytics import YOLO
from PIL import Image
import numpy as np
from dotenv import load_dotenv
from Adafruit_IO import Client

# Load environment variables
load_dotenv()

# --- Khởi tạo Adafruit IO client ---
AIO_USERNAME = os.getenv("AIO_USERNAME")
AIO_KEY      = os.getenv("AIO_KEY")
AIO_FEED     = "yolofarm.farm-status"
aio = Client(AIO_USERNAME, AIO_KEY)

# Initialize YOLO model once
yolo_model = YOLO("models/best.pt")

# Streamlit page config
st.set_page_config(
    page_title="Seasonal Analysis",
    layout="wide"
)

# Route guard (assumes login state in session)
if not st.session_state.get("logged_in", False):
    st.switch_page("pages/Login.py")

# Custom CSS
custom_css = """
<style>
/* Ẩn menu và footer mặc định của Streamlit */
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
body { background-color: #F7F7F7; font-family: 'sans-serif'; }
h1, h2, h3, h4 { color: #333333; }
.float-button { position: fixed; bottom: 20px; right: 20px; background-color: #4E7B70; color: white; border-radius: 50%; width: 100px; height: 100px; border: none; text-align: center; cursor: pointer; font-size: 1rem; box-shadow: 2px 2px 5px rgba(0,0,0,0.3); }
.float-button span { display: inline-block; margin-top: 35px; font-size: 1rem; font-weight: bold; }
.float-button:hover { background-color: #3D6157; }
.notified-blog { background-color: #FFFFFF; border-radius: 10px; padding: 20px; box-shadow: 0 0 5px rgba(0,0,0,0.1); }
.notified-blog h3 { margin-top: 0; }
</style>
"""
st.markdown(custom_css, unsafe_allow_html=True)

# Prepare log file
dirs = os.makedirs("logs", exist_ok=True)
log_file = "logs/detect_log.csv"
if not os.path.exists(log_file) or os.path.getsize(log_file) == 0:
    pd.DataFrame(columns=["datetime", "image_path", "result_path"]).to_csv(log_file, index=False)

col1, col2 = st.columns([3, 1], gap="large")

# Prediction + report function
def predict_and_report(source_path: str):
    # Run prediction via Python API for count of boxes
    res = yolo_model(source_path)[0]
    # Save annotated image
    img_annotated = res.plot()
    output_dir = f"detect/predict_{uuid.uuid4().hex[:6]}"
    os.makedirs(os.path.join("detect", output_dir), exist_ok=True)
    result_path = os.path.join("detect", output_dir, os.path.basename(source_path))
    Image.fromarray(img_annotated).save(result_path)
    
    # Determine status based on detections
    detected_classes = [res.names[int(cls)] for cls in res.boxes.cls]
    status = "Bệnh" if any(cls_name.lower() != 'tomato healthy' for cls_name in detected_classes) else "Bình thường"
    
    # Send status to Adafruit IO
    try:
        aio.send_data(AIO_FEED, status)
    except Exception as e:
        st.warning(f"Không gửi trạng thái lên Adafruit IO: {e}")
    
    return result_path, status

with col1:
    st.title("Phát hiện bệnh với YOLOv8")
    
    with st.expander("📜 Lịch sử phát hiện bệnh"):
        log_df = pd.read_csv(log_file)
        if not log_df.empty:
            for _, row in log_df[::-1].head(8).iterrows():
                st.markdown(f"**🕒 {row['datetime']}**")
                c1, c2 = st.columns(2)
                with c1:
                    st.image(row['image_path'], caption="Ảnh gốc", width=200)
                with c2:
                    st.image(row['result_path'], caption="Kết quả", width=200)
                st.markdown("---")
        else:
            st.info("Chưa có log nào được ghi nhận.")

    uploaded_file = st.file_uploader("Chọn một ảnh (jpg, png)", type=["jpg", "png"])
    if uploaded_file is not None:
        temp_dir = "temp_uploads"
        os.makedirs(temp_dir, exist_ok=True)
        temp_img_path = os.path.join(temp_dir, uploaded_file.name)
        with open(temp_img_path, "wb") as f:
            f.write(uploaded_file.getbuffer())

        st.image(temp_img_path, caption="Ảnh đã tải lên", use_container_width=True)
        
        # Prediction and send report
        result_path, status = predict_and_report(temp_img_path)
        
        if os.path.exists(result_path):
            st.image(result_path, caption=f"Ảnh kết quả YOLO ({status})", use_container_width=True)
            # Log
            log_df = pd.read_csv(log_file)
            log_df.loc[len(log_df)] = {
                "datetime": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "image_path": temp_img_path,
                "result_path": result_path
            }
            log_df.to_csv(log_file, index=False)
        else:
            st.warning("Không tìm thấy ảnh kết quả. Vui lòng kiểm tra model hoặc ảnh input.")

with col2:
    st.markdown("### Notified Blog")
    bullet_points = [
        "Detect yellow leaves at cam0",
        "Detect leaves are rotten at cam1",
        "Detect ripe tomatoes at cam2",
        "Detect ripe tomatoes at cam3",
        "Detect yellow leaves at cam7",
        "Detect yellow leaves at cam8"
    ]
    for idx, point in enumerate(bullet_points, start=1):
        st.markdown(f"{idx}. {point}")

    if st.button("Dashboard", key="btn_cp"):
        st.switch_page("./main.py")

