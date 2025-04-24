import streamlit as st
import requests

API_URL = "http://localhost:5000/users"  # Đổi lại nếu Flask chạy ở chỗ khác

st.title("🔐 Đăng nhập")

username = st.text_input("Tên đăng nhập")
password = st.text_input("Mật khẩu", type="password")

def fetch_users():
    try:
        response = requests.get(API_URL)
        if response.status_code == 200:
            return response.json()
        else:
            st.error("Không lấy được danh sách người dùng từ server.")
            return []
    except Exception as e:
        st.error(f"Lỗi kết nối đến API: {e}")
        return []

if st.button("Đăng nhập"):
    users = fetch_users()
    matched_user = next((u for u in users if u["username"] == username and u["password"] == password), None)

    if matched_user:
        st.session_state.logged_in = True
        st.session_state.username = username
        st.success("Đăng nhập thành công!")
        st.switch_page("Home.py")
    else:
        st.error("Sai thông tin đăng nhập")
