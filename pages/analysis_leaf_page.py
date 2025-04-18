import streamlit as st
import pandas as pd
import subprocess
import os
import uuid

import streamlit as st
from ultralytics import YOLO
from PIL import Image
from datetime import datetime
import numpy as np

st.set_page_config(
    page_title="Seasonal Analysis",
    layout="wide"
)

custom_css = """
<style>
/* Ẩn menu và footer mặc định của Streamlit (nếu muốn) */
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}

/* Tùy chỉnh chung */
body {
    background-color: #F7F7F7;
    font-family: 'sans-serif';
}

/* Tùy chỉnh tiêu đề */
h1, h2, h3, h4 {
    color: #333333;
}

/* Nút nổi (Floating Action Button) ở góc phải dưới */
.float-button {
    position: fixed;
    bottom: 20px;
    right: 20px;
    background-color: #4E7B70;
    color: white;
    border-radius: 50%;
    width: 100px;
    height: 100px;
    border: none;
    text-align: center;
    cursor: pointer;
    font-size: 1rem;
    box-shadow: 2px 2px 5px rgba(0,0,0,0.3);
}
.float-button span {
    display: inline-block;
    margin-top: 35px; /* canh text ở giữa nút */
    font-size: 1rem;
    font-weight: bold;
}
.float-button:hover {
    background-color: #3D6157;
}

/* Tùy chỉnh cột phải: Notified Blog */
.notified-blog {
    background-color: #FFFFFF;
    border-radius: 10px;
    padding: 20px;
    box-shadow: 0 0 5px rgba(0,0,0,0.1);
}
.notified-blog h3 {
    margin-top: 0;
}
</style>
"""
st.markdown(custom_css, unsafe_allow_html=True)

# === Tạo file log nếu chưa có hoặc file rỗng ===
log_file = "logs/detect_log.csv"
os.makedirs("logs", exist_ok=True)

# Nếu file không tồn tại hoặc rỗng -> tạo header
if not os.path.exists(log_file) or os.path.getsize(log_file) == 0:
    pd.DataFrame(columns=["datetime", "image_path", "result_path"]).to_csv(log_file, index=False)


col1, col2 = st.columns([3, 1], gap="large")

def predict_model(source_path: str):
    print("Starting prediction...")
    # Đặt tên thư mục output riêng biệt nếu muốn (tránh đè)
    output_dir = f"detect/predict_{uuid.uuid4().hex[:6]}"

    predict_command = f'yolo detect predict model=models/best.pt source="{source_path}" project=detect name={output_dir} exist_ok=True'

    subprocess.run(predict_command, shell=True)

    # Dự đoán xong thì ảnh output nằm trong: runs/detect/predict_xxxx/{tên_ảnh}
    filename = os.path.basename(source_path)
    output_img_path = os.path.join("detect", output_dir, filename)
    return output_img_path

with col1:
    # st.markdown("### Seasonal Analysis")

   
    # image_dir = "images"
    # image_files = [f for f in os.listdir(image_dir) if f.endswith(('.png', '.jpg', '.jpeg'))]


    # image_cols = st.columns(5)


    # for idx, img_name in enumerate(image_files):
    #     img_path = os.path.join(image_dir, img_name)  
    #     with image_cols[idx % 5]:  
    #         st.image(img_path)


    # data = {
    #     "Ngày": ["1/2/2025", "2/2/2025", "3/2/2025", "4/2/2025", "5/2/2025"],
    #     "Sản lượng (Kg)": [120, 130, 115, 140, 160],
    #     "Chất lượng (%)": [85, 80, 88, 82, 90],
    #     "Độ ẩm đất (%)": [60, 62, 58, 65, 70],
    #     "Nhiệt độ (°C)": [25, 26, 24, 27, 28],
    #     "Số cây bị bệnh": [2, 3, 1, 4, 0],
    #     "Ghi chú": ["Bình thường", "Đột biến", "Bình thường", "Đột biến", "Bình thường"]
    # }
    # df = pd.DataFrame(data)

    # st.data_editor(df, num_rows="dynamic")  

    st.title("Phát hiện bệnh với YOLOv8")


    # with st.expander("📜 Lịch sử phát hiện bệnh"):
    #     log_df = pd.read_csv(log_file)
    #     if not log_df.empty:
    #         for i, row in log_df[::-1].head(5).iterrows():  # 5 log gần nhất
    #             st.markdown(f"**🕒 {row['datetime']}**")
    #             cols = st.columns([1, 1])
    #             with cols[0]:
    #                 st.image(row["image_path"], caption="Ảnh gốc", use_container_width=True)
    #             with cols[1]:
    #                 st.image(row["result_path"], caption="Kết quả", use_container_width=True)
    #             st.markdown("---")
    #     else:
    #         st.info("Chưa có log nào được ghi nhận.")
    with st.expander("📜 Lịch sử phát hiện bệnh"):
        log_df = pd.read_csv(log_file)
        if not log_df.empty:
            for i, row in log_df[::-1].head(8).iterrows():  # hiển thị 8 log gần nhất
                st.markdown(f"**🕒 {row['datetime']}**")
                cols = st.columns([1, 1])
                with cols[0]:
                    st.image(row["image_path"], caption="Ảnh gốc", width=200)
                with cols[1]:
                    st.image(row["result_path"], caption="Kết quả", width=200)
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

        # Dự đoán bằng CLI
        output_img_path = predict_model(temp_img_path)

        if os.path.exists(output_img_path):
            st.image(output_img_path, caption="Ảnh kết quả YOLO", use_container_width=True)
            # Ghi log
            log_df = pd.read_csv(log_file)
            log_df.loc[len(log_df)] = {
                "datetime": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "image_path": temp_img_path,
                "result_path": output_img_path
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
    
    st.markdown("</div>", unsafe_allow_html=True)
    
    with st.container():
        _, col2 = st.columns([3, 1.5])
        with col2:
            if st.button("Dashboard", key="btn_cp"):
                st.switch_page("./main.py")


