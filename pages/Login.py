import streamlit as st

VALID_USERS = {"admin": "123456"}

st.title("🔐 Đăng nhập")

username = st.text_input("Tên đăng nhập")
password = st.text_input("Mật khẩu", type="password")

if st.button("Đăng nhập"):
    if username in VALID_USERS and VALID_USERS[username] == password:
        st.session_state.logged_in = True
        st.session_state.username = username
        st.success("Đăng nhập thành công!")
        st.switch_page("Home.py")
    else:
        st.error("Sai thông tin đăng nhập")
