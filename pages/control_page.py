import streamlit as st
import datetime


st.set_page_config(page_title="Watering Dashboard", layout="wide")


st.markdown("""
<style>
/* Ẩn menu và footer mặc định */
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}

/* Màu nền tổng thể */
body {
    background-color: #F0F0F0;
    font-family: "Arial", sans-serif;
}

/* Nút nổi (WaterButton) ở cạnh trái */
.floating-water-button {
    position: fixed;
    top: 120px; /* điều chỉnh vị trí theo ý muốn */
    left: 20px;
    width: 80px;
    height: 80px;
    border-radius: 20px;
    background-color: #C2DAD3; /* màu nền */
    box-shadow: 2px 2px 5px rgba(0,0,0,0.2);
    text-align: center;
    cursor: pointer;
}
.floating-water-button p {
    margin: 0;
    padding-top: 15px;
    color: #333;
    font-weight: bold;
    font-size: 0.9rem;
}

/* Khối Add new ở trên (mô phỏng popup/card) */
.add-new-container {
    background-color: #AFCBB9;
    border-radius: 10px;
    padding: 20px;
    margin-bottom: 20px;
    color: #333;
    box-shadow: 0 1px 4px rgba(0,0,0,0.1);
    width: 320px; /* tùy chỉnh */
}

/* Tiêu đề nhỏ */
.add-new-container h3 {
    margin-top: 0;
    margin-bottom: 10px;
}

/* Các label, input (mặc định Streamlit), có thể thêm style nếu cần */
</style>
""", unsafe_allow_html=True)


moisture = 50
col1, col2, col3 = st.columns([1.2, 1.5, 1.5])


with col1:
    st.markdown(f"### Current soil moisture: {moisture}%")
    st.progress(moisture)  

    st.markdown("#### Watering History")

    watering_history = [
        "1/20 10:00 to 11:00",
        "1/21 08:00 to 09:00",
        "1/23 16:00 to 17:00",
        "1/24 09:30 to 10:00",
        "1/25 10:00 to 10:30"
    ]
    for wh in watering_history:
        st.markdown(f"- {wh}")
        
    col1, _ = st.columns([1.5, 3])
    with col1:
        if st.button("Dashboard"):
            st.switch_page("./main.py")

with col2:
    st.markdown("### Watering Schedule")

    schedule_data = [
        {"date": "2/2 Thu", "time": "20:00"},
        {"date": "2/3 Fri", "time": "21:00"},
        {"date": "2/4 Sat", "time": "18:00"},
        {"date": "2/5 Sun", "time": "19:00"},
    ]
    if "schedule_data" not in st.session_state:
        st.session_state.schedule_data = [
            {"date": "2/2 Thu", "time": "20:00"},
            {"date": "2/3 Fri", "time": "21:00"},
            {"date": "2/4 Sat", "time": "18:00"},
            {"date": "2/5 Sun", "time": "19:00"},
        ]
    col1, col2 = st.columns([2, 1])
    with col1:
        for item in st.session_state.schedule_data:
            st.markdown(f"- **{item['date']}** at **{item['time']}**")

    date = st.date_input("Enter Date")
    time = st.time_input("Enter Time")
    with col2:
        if st.button("➕ Add"):
            if date and time:
                st.session_state.schedule_data.append({"date": date, "time": time})
                st.rerun()  
            else:
                st.warning("Please enter both date and time!")

with col3:
    st.markdown("### Entire Map")

    st.image("images/map.jpg")

    st.markdown("### Watering Suggestion")
    suggestions = [
        "Hazard Day: Soil dryness -> run irrigation 3h",
        "Check sensor 1 for unusual moisture drop",
        "Sensor2 has no responses, maybe broken?"
    ]
    for idx, sug in enumerate(suggestions, start=1):
        st.markdown(f"{idx}. {sug}")



