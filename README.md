﻿# CO3107

<!-- Trang cà chua -->
#  Trang Phân Tích Sự Chín của Cà Chua 🍅

Trang này là một phần trong hệ thống giám sát nông nghiệp thông minh, được phát triển bằng **Streamlit**. Mục tiêu của trang là hỗ trợ nông dân hoặc hệ thống nông nghiệp tự động trong việc **theo dõi và đánh giá độ chín của cà chua** thông qua ảnh chụp từ camera hoặc ảnh tải lên.


## 🎯 Mục Tiêu
- Tự động phát hiện và phân loại cà chua chín / chưa chín trong ảnh.
- Hỗ trợ giám sát sự phát triển của cây trồng theo thời gian.
- Trực quan hóa dữ liệu hỗ trợ ra quyết định nông nghiệp chính xác hơn.


## 🔍 Các Tính Năng Chính

### 🖼️ 1. Hiển thị ảnh từ camera
- Ảnh được lấy từ thư mục `images/tomatoes/uploaded`.
- Hiển thị theo dạng lưới có thể điều chỉnh.

### 📤 2. Tải ảnh và dự đoán
- Người dùng có thể **tải ảnh cà chua** để hệ thống phân tích.
- Ảnh sẽ được đưa vào mô hình YOLO để phát hiện từng quả cà chua.
- Sau đó, từng quả được phân loại bởi mô hình ResNet50 thành **Chín (Ripe)** hoặc **Chưa chín (Unripe)**.
- Kết quả trực quan hóa trên ảnh: viền màu xanh dương cho quả chín, màu xanh lá cho quả chưa chín.

### 📊 3. Bảng dữ liệu theo dõi
  - Ngày
  - Tổng số quả phát hiện
  - Tỉ lệ quả chín
  - Gợi ý hành động: Thu hoạch / Cần thời gian

### 📝 4. Lấy dữ liệu thông qua camera
- Lấy hình ảnh thực tế thông qua camera của thiết bị.
- Nhấn s để chụp ảnh, q để thoát.
- Hiển thị sự phát hiện đồng thời phân loại cà chua trong ảnh đó.

<!-- ### 📝 4. Blog nhật ký phát hiện
- Cập nhật theo thời gian thực số lượng cà chua chín được phát hiện từ các camera khác nhau.
- Hiển thị theo định dạng danh sách dễ theo dõi.

### 🔁 5. Nút chuyển về dashboard
- Cho phép người dùng nhanh chóng trở về trang tổng quan của hệ thống (`main.py`). -->



## 🧩 Công Nghệ Sử Dụng

| Công nghệ | Mục đích |
|----------|---------|
| Streamlit | Xây dựng giao diện người dùng |
| YOLO (Ultralytics) | Phát hiện vật thể trong ảnh |
| ResNet50 | Phân loại ảnh thành chín / chưa chín |
| Torch / torchvision | Xử lý mô hình AI |
| OpenCV & PIL | Xử lý ảnh |
| Pandas | Hiển thị và chỉnh sửa bảng dữ liệu |
| Adafruit_IO | Gửi và nhận tín hiệu từ Adafruit |


## 🗂 Cấu Trúc Mô Hình

- `tomato_detection_model.pt` – Mô hình YOLO tùy chỉnh để phát hiện cà chua.
- `tomato_classifier.pth` – Mô hình ResNet50 để phân loại độ chín.
<!-- Hết trang cà chua -->

