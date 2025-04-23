import os
import cv2
import torch
import pandas as pd
from collections import defaultdict
from datetime import datetime, timedelta
from PIL import Image
import streamlit as st
import matplotlib.pyplot as plt
from ultralytics import YOLO
from torchvision import transforms, models
from Adafruit_IO import Client
import torch.nn as nn


# Define something to get and set data on adafruit
AIO_USERNAME = os.getenv("AIO_USERNAME")
AIO_KEY = os.getenv("AIO_KEY")
aio = Client(AIO_USERNAME, AIO_KEY)

STATUS_ID = "yolofarm.farm-status"
# TEMPERATURE_ID = "yolofarm.farm-temperature"
# SOIL_MOISTURE_ID = "yolofarm.farm-soil-moisture"
# ------------------------------------------------

# some path for prediction model
device = torch.device('cpu')
transform = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize([0.485, 0.456, 0.406],
                         [0.229, 0.224, 0.225])
])

base_dir = os.path.dirname(__file__)
pt_path = os.path.join(base_dir, "../models/tomato_detection_model.pt")
pth_path = os.path.join(base_dir, "../models/tomato_classifier.pth")

detection_model = YOLO(pt_path)
classifier = models.resnet50(weights=None)
classifier.fc = nn.Linear(classifier.fc.in_features, 2)
classifier.load_state_dict(torch.load(pth_path, map_location=device))
classifier.to(device)
# ------------------------------------------------
class Ada:

    # Send data 'Chín' or 'Chưa chín' to adafruit
    def send_to_adafruit(self, value, feed_name=STATUS_ID):
        try:
            aio.send(feed_name, value)
            print(f"Gửi thành công: {value} đến {feed_name}")
        except Exception as e:
            print("Lỗi gửi dữ liệu:", e)

    # Get data from adafruit to display in the table
    def get_feed_data(self, feed_key, max_results=100):
        try:
            data = aio.data(feed_key, max_results=max_results)
            return data
        except Exception as e:
            print("Lỗi lấy dữ liệu từ feed:", e)
            return []

    # Group data by day and calculate average
    def group_avg_by_day(self, feed_data):
        daily_values = defaultdict(list)
        for item in feed_data:
            # Standard to VietNam timezone
            dt = datetime.fromisoformat(item.created_at.replace("Z", "+00:00")) + timedelta(hours=7)
            day_str = dt.strftime("%d/%m/%Y")
            try:
                val = float(item.value)
                daily_values[day_str].append(val)
            except:
                continue

        return {day: round(sum(vals)/len(vals), 1) for day, vals in daily_values.items()}

    # Group and format after to apply for table
    def group_and_format_data(self, feed_status):
        
        # Group data of tomatoes by day
        daily_counts = defaultdict(lambda: {"Chín": 0, "Chưa chín": 0})
        for item in feed_status:
            if item.value not in ["Chín", "Chưa chín"]:
                continue
            # Standard to VietNam timezone, +7 (17h (ada) -> 24h (Viet Nam))
            dt = datetime.fromisoformat(item.created_at.replace("Z", "+00:00")) + timedelta(hours=7)
            day_str = dt.strftime("%d/%m/%Y")
            daily_counts[day_str][item.value] += 1

        # Construct dataframe
        df = pd.DataFrame([
            {
                "Ngày": day,
                "Số quả phát hiện (quả)": counts["Chín"] + counts["Chưa chín"],
                "Số quả chín": counts["Chín"],
                "Số quả chưa chín": counts["Chưa chín"]
            }
            for day, counts in daily_counts.items()
        ])
        df["Ngày_datetime"] = pd.to_datetime(df["Ngày"], dayfirst=True)
        df = df.sort_values(by="Ngày_datetime", ascending=False).head(5)
        df = df.sort_values(by="Ngày_datetime")
        df["Tỉ lệ quả chín (%)"] = (df["Số quả chín"] / df["Số quả phát hiện (quả)"] * 100).round(0).astype(int)

        df["Ghi chú"] = df["Tỉ lệ quả chín (%)"].apply(self.generate_note)

        # # Get temperature and soil_moisture
        # temp_avg = self.group_avg_by_day(feed_temperature)
        # soil_avg = self.group_avg_by_day(feed_soil)

        # df["Độ ẩm đất (%)"] = df["Ngày"].apply(lambda d: soil_avg.get(d, 'Không có dữ liệu cho ngày này'))
        # df["Nhiệt độ (°C)"] = df["Ngày"].apply(lambda d: temp_avg.get(d, 'Không có dữ liệu cho ngày này'))


        return {
            "Ngày": df["Ngày"].tolist(),
            "Số quả phát hiện (quả)": df["Số quả phát hiện (quả)"].tolist(),
            "Tỉ lệ quả chín (%)": df["Tỉ lệ quả chín (%)"].tolist(),
            # "Độ ẩm đất (%)": df["Độ ẩm đất (%)"].tolist(),
            # "Nhiệt độ (°C)": df["Nhiệt độ (°C)"].tolist(),
            "Ghi chú": df["Ghi chú"].tolist()
        }

    # Simulate the actions if farmer need to do :))
    def generate_note(self, ti_le):
        if ti_le >= 80:
            return "Cần thu hoạch gấp"
        elif ti_le >= 60:
            return "Có thể thu hoạch"
        else:
            return "Chưa chín nhiều"

class Page:
    def __init__(self, title='Phân tích sự chín của cà chua', layout="wide"):
        st.set_page_config(
            page_title=title,
            layout=layout
        )

    def custom_css(self, custom = 
        """
            <style>
                #MainMenu {visibility: hidden;}
                footer {visibility: hidden;}

                body {
                    margin: 0;
                    padding: 0;
                    background-color: #F7F7F7;
                    font-family: 'sans-serif';
                    color: #e0e0e0;
                }

                h1, h2, h3, h4 {
                    color: #333333;
                }
                
                h1 {
                    font-size: 2rem;
                }
                h2 {
                    font-size: 1.7rem;
                }
                h3 {
                    font-size: 1.4rem;
                }
                h4 {
                    font-size: 1.2rem;
                }
                p, li, td, th {
                    font-size: 1.05rem;
                }
                
                img {
                    border-radius: 6px;
                    box-shadow: 0 1px 3px rgba(0,0,0,0.3);
                    transition: transform 0.3s ease, box-shadow 0.3s ease;
                }
                img:hover {
                    transform: scale(1.05);
                    box-shadow: 0 4px 8px rgba(0,0,0,0.5);
                }

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
                    margin-top: 35px;
                    font-size: 1rem;
                    font-weight: bold;
                }
                .float-button:hover {
                    background-color: #3D6157;
                }
            </style>
        """
        ):
        st.markdown(custom, unsafe_allow_html=True)
    
    def grid(self, grid = [2, 1], gap="large"):
        return st.columns(spec=grid, gap=gap)

class Tomato:
    def __init__(self, title = 'Phân tích sự chín của cà chua trong nông trại'):
        self.title = title


    def predict_ripeness(self, image_path, adafruit, detection_model=detection_model, classifier=classifier, transform=transform, device=device):
        image = cv2.imread(image_path)
        if image is None:
            print(f"Tải ảnh không được: {image_path}")
            return
        
        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        ripe_count = 0
        unripe_count = 0
        
        results = detection_model(image_path, conf=0.5, iou=0.6)
        boxes = results[0].boxes.xyxy.cpu().numpy()
        for i, box in enumerate(boxes):
            x1, y1, x2, y2 = map(int, box)
            crop = image_rgb[y1:y2, x1:x2]
            if crop.size == 0:
                print(f"Bỏ qua cắt ảnh {i} trong {image_path}")
                continue
            
            crop_pil = Image.fromarray(crop)
            crop_tensor = transform(crop_pil).unsqueeze(0).to(device)
            
            classifier.eval()
            with torch.no_grad():
                output = classifier(crop_tensor)
                _, predicted = torch.max(output, 1)
                is_ripe = 0 if predicted.item() else 1
                label = 'Ripe' if is_ripe else 'Unripe'
                color = (255, 0 , 0) if is_ripe else (0, 255, 0)
                
                if is_ripe:
                    ripe_count += 1
                else:
                    unripe_count += 1
                
            cv2.rectangle(image, (x1, y1), (x2, y2), color, 2)
            cv2.putText(image, label, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, color, 2)
            
        fig, ax = plt.subplots(figsize=(10, 10))
        ax.imshow(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
        ax.set_title(f'Dự đoán cho ảnh vừa tải lên')
        ax.axis('off')
        st.pyplot(fig)
        
        st.success(f"🍅 Số quả chín: {ripe_count}")
        st.warning(f"🥒 Số quả chưa chín: {unripe_count}")        
        adafruit.send_to_adafruit('Chín' if ripe_count >= unripe_count else 'Chưa chín')
        

    def show_img_capture(self, images_path, images_per_row, fixed_size=250):
        st.markdown(f"## Một số hình ảnh được chụp và tải lên")
        image_files = [f for f in os.listdir(images_path) if f.endswith(('.png', '.jpg', '.jpeg'))]
        image_files = image_files[:images_per_row * 2] # limit to 2 rows
        image_cols = st.columns(images_per_row)
        for idx, img_name in enumerate(image_files):
            img_path = os.path.join(images_path, img_name)  
            with image_cols[idx % images_per_row]:
                try:
                    img = Image.open(img_path).convert("RGB")
                    img = img.resize((fixed_size, fixed_size))
                    st.image(img)
                except:
                    st.error(f"Không thể hiển thị ảnh: {img_name}")

    def load_img(self, adafruit):
        uploaded_file = st.file_uploader("Chọn một ảnh (jpg, png)", type=["jpg", "png"])
        if uploaded_file is not None:

            image = Image.open(uploaded_file).convert("RGB")

            target_folder = os.path.join("images", "tomatoes", "uploaded")
            os.makedirs(target_folder, exist_ok=True)

            save_path = os.path.join(target_folder, datetime.now().strftime("%H%M%S_%d%m%y.jpg"))
            image.save(save_path)
            
            st.image(image, caption="Ảnh đã tải lên", use_container_width=True)

            self.predict_ripeness(save_path, adafruit)
    
    def data_table(self, adafruit, feed_status):
        st.markdown(f"## Thống kê dữ liệu thu được những ngày qua")

        df = pd.DataFrame(adafruit.group_and_format_data(feed_status))

        st.data_editor(df, num_rows="dynamic")

        st.title("Phát hiện cà chua đã chín hay chưa")
    
    def capture_image_from_camera(self, save_dir="images/tomatoes/camera"):

        os.makedirs(save_dir, exist_ok=True)

        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            print("Không thể mở camera")
            return None

        print("Camera đã bật. Nhấn 's' để chụp và lưu ảnh, 'q' để thoát không lưu.")

        while True:
            ret, frame = cap.read()
            if not ret:
                print("Không lấy được hình ảnh từ camera")
                break

            cv2.imshow("CAMERA - PRESS 's' TO CAPTURE, OR 'q' TO EXIT", frame)
            key = cv2.waitKey(1) & 0xFF

            if key == ord('s'):
                filename = datetime.now().strftime("%H%M%S_%d%m%y.jpg")
                save_path = os.path.join(save_dir, filename)
                cv2.imwrite(save_path, frame)
                print(f"Đã lưu ảnh tại: {save_path}")
                cap.release()
                cv2.destroyAllWindows()
                return save_path

            elif key == ord('q'):
                print("Thoát không lưu ảnh.")
                break

        cap.release()
        cv2.destroyAllWindows()
        return None


class Blog:
    def __init__(self, title = 'Thông báo'):
        st.markdown(f"## {title}")

    def blog(self, 
        data = [
        "Phát hiện 2 cà chua chín tại cam1",
        "Phát hiện 5 cà chua chín tại cam0",
        "Phát hiện 2 cà chua chín tại cam6",
        "Phát hiện 3 cà chua chín tại cam2",
        "Phát hiện 7 cà chua chín tại camk",
        "Phát hiện 1 cà chua chín tại cam4"
        ]):
        
        for idx, point in enumerate(data, start=1):
            st.markdown(f'<p style="font-size: 1.3rem; line-height: 1.6;">{idx}. {point}</p>', unsafe_allow_html=True)

        st.markdown("</div>", unsafe_allow_html=True)

    def to_dashboard(self):
        with st.container():
            _, col2 = st.columns([3, 2])
            with col2:
                if st.button("Dashboard", key="btn_cp"):
                    st.switch_page("./main.py")

# Start page here

if not st.session_state.logged_in:
    st.switch_page("pages/Login.py")

page = Page()
page.custom_css()

# option params: (grid = [int]; gap in ["small", "medium", "large"])
col1, col2 = page.grid()
tomato = Tomato()
adafruit = Ada()

with col1:
    st.markdown(f"# {tomato.title}")
    feed_status = adafruit.get_feed_data(STATUS_ID)
    # feed_temperature = adafruit.get_feed_data(TEMPERATURE_ID)
    # feed_soil = adafruit.get_feed_data(SOIL_MOISTURE_ID)

    tomato.show_img_capture(images_path="images/tomatoes/uploaded", images_per_row=6)

    tomato.data_table(adafruit, feed_status)
    tomato.load_img(adafruit)
    
    

with col2:
    st.markdown(f"## Nhận diện và phân loại cà chua qua camera")
    if st.button('Nhấn để mở camera'):
        tomato.predict_ripeness(tomato.capture_image_from_camera(), adafruit)
#     blog = Blog()
#     # option params: (data = [str])
#     blog.blog()
#     blog.to_dashboard()