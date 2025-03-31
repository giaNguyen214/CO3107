import streamlit as st
import pandas as pd
import os

import streamlit as st
from ultralytics import YOLO
from PIL import Image
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

col1, col2 = st.columns([3, 1], gap="large")

with col1:
    st.markdown("### Seasonal Analysis")

   
    image_dir = "images"
    image_files = [f for f in os.listdir(image_dir) if f.endswith(('.png', '.jpg', '.jpeg'))]


    image_cols = st.columns(5)


    for idx, img_name in enumerate(image_files):
        img_path = os.path.join(image_dir, img_name)  
        with image_cols[idx % 5]:  
            st.image(img_path)


    data = {
        "Ngày": ["1/2/2025", "2/2/2025", "3/2/2025", "4/2/2025", "5/2/2025"],
        "Sản lượng (Kg)": [120, 130, 115, 140, 160],
        "Chất lượng (%)": [85, 80, 88, 82, 90],
        "Độ ẩm đất (%)": [60, 62, 58, 65, 70],
        "Nhiệt độ (°C)": [25, 26, 24, 27, 28],
        "Số cây bị bệnh": [2, 3, 1, 4, 0],
        "Ghi chú": ["Bình thường", "Đột biến", "Bình thường", "Đột biến", "Bình thường"]
    }
    df = pd.DataFrame(data)

    st.data_editor(df, num_rows="dynamic")  

    st.title("Phát hiện quả cà chua với YOLOv8")


    uploaded_file = st.file_uploader("Chọn một ảnh (jpg, png)", type=["jpg", "png"])
    if uploaded_file is not None:

        image = Image.open(uploaded_file)
        st.image(image, caption="Ảnh đã tải lên", use_column_width=True)

        
        image_array = np.array(image)


        model = YOLO("trained.h5") 


        results = model(image_array)

       
        annotated_image = results[0].plot()

        st.image(annotated_image, caption="Ảnh kết quả", use_column_width=True)


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


