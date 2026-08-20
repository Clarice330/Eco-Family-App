# -*- coding: utf-8 -*-
"""
🍀 絲野仙蹤 (Eco-Family) - 澳門親子綠色呼吸智慧康旅導航系統
"""

import streamlit as st
import pandas as pd
import requests
import urllib.parse
import time
import math
from datetime import datetime

# ==================== 1. 全域 Session State 安全初始化 ====================
query_params = st.query_params

if "page" in query_params and query_params["page"]:
    st.session_state.current_page = query_params["page"]

# 長者模式開關 (預設關閉)
if "senior_mode" not in st.session_state:
    st.session_state.senior_mode = False

if "global_temp" not in st.session_state:
    st.session_state.global_temp = 22.5
if "global_uv" not in st.session_state:
    st.session_state.global_uv = 1.2
if "global_rain" not in st.session_state:
    st.session_state.global_rain = False
if "global_wind" not in st.session_state:
    st.session_state.global_wind = 10.0
if "global_pm25" not in st.session_state:
    st.session_state.global_pm25 = 12.0  # PM2.5 微粒 (μg/m³)
if "global_pm10" not in st.session_state:
    st.session_state.global_pm10 = 24.0  # PM10 懸浮微粒 (μg/m³)
if "global_aqi" not in st.session_state:
    st.session_state.global_aqi = 28.0   # 空氣質量指數 (AQI)

if "override_weather" not in st.session_state:
    st.session_state.override_weather = False

# 讀取真實 GPS 座標
if "lat" in query_params and "lon" in query_params:
    try:
        st.session_state.my_lat = float(query_params["lat"])
        st.session_state.my_lon = float(query_params["lon"])
    except ValueError:
        pass

# 使用者 GPS 座標 (預設澳門座標)
if "my_lat" not in st.session_state:
    st.session_state.my_lat = 22.1568
if "my_lon" not in st.session_state:
    st.session_state.my_lon = 113.5615

# 聲波驅蟲狀態與記憶
if "audio_active" not in st.session_state:
    st.session_state.audio_active = False
if "selected_insect_freq" not in st.session_state:
    st.session_state.selected_insect_freq = "17.4 kHz - 模擬雄蚊翅聲 (驅避咬人母蚊)"

# 預設暱稱 (SOS 系統使用)
if "user_nickname" not in st.session_state:
    st.session_state.user_nickname = ""

# 導航頁面狀態
if "current_page" not in st.session_state:
    st.session_state.current_page = "menu"

# 頁面配置
st.set_page_config(
    page_title="絲野仙蹤 Eco-Family",
    page_icon="🍀",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# ==================== 2. 全局 CSS 樣式美化 (支援長者動態大字版) ====================
is_senior = st.session_state.senior_mode

# 動態調整字體大小與間距變數
btn_font_size = "1.85rem" if is_senior else "1.35rem"
btn_height = "90px" if is_senior else "76px"
text_base_size = "1.25rem" if is_senior else "0.9rem"
title_base_size = "2.1rem" if is_senior else "1.55rem"
metric_val_size = "1.8rem" if is_senior else "1.35rem"

st.markdown(f"""
<style>
    .stApp {{
        background-color: #F7FAF8;
        color: #111111;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
    }}
    
    /* 隱藏原生側邊欄 */
    section[data-testid="stSidebar"] {{
        display: none;
    }}

    /* 功能按鈕容器寬度與邊距強制對齊 */
    div[data-testid="stButton"], div[data-testid="stLinkButton"] {{
        width: 100% !important;
        margin: 0 0 16px 0 !important;
        padding: 0 !important;
        box-sizing: border-box !important;
    }}

    /* 功能按鈕 100% 強制像素級長度、高度與樣式完全對齊 */
    div[data-testid="stButton"] > button, div[data-testid="stLinkButton"] > a {{
        width: 100% !important;
        background-color: #FFFFFF !important;
        color: #1B5E20 !important;
        border-radius: 16px !important;
        height: {btn_height} !important;
        min-height: {btn_height} !important;
        max-height: {btn_height} !important;
        box-shadow: 0 4px 15px rgba(0,0,0,0.06) !important;
        border: 2px solid #C8E6C9 !important;
        text-align: center !important;
        font-size: {btn_font_size} !important;
        font-weight: 800 !important;
        margin: 0 0 16px 0 !important;
        padding: 0 !important;
        transition: all 0.2s ease-in-out !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        text-decoration: none !important;
        border-bottom: none !important;
        box-sizing: border-box !important;
        line-height: 1.2 !important;
    }}

    div[data-testid="stButton"] > button:hover, div[data-testid="stLinkButton"] > a:hover {{
        border-color: #2E7D32 !important;
        box-shadow: 0 6px 20px rgba(46,125,50,0.2) !important;
        background-color: #F1F8E9 !important;
        transform: translateY(-2px) !important;
        color: #1B5E20 !important;
        text-decoration: none !important;
    }}

    /* 頂部 Header 求救按鈕特化樣式 */
    .sos-header-btn button {{
        background-color: #FFEBEE !important;
        color: #C62828 !important;
        border: 2px solid #FFCDD2 !important;
        font-weight: 800 !important;
        height: 42px !important;
        min-height: 42px !important;
        font-size: {"1.05rem" if is_senior else "0.85rem"} !important;
        border-radius: 8px !important;
        padding: 4px 8px !important;
        margin-bottom: 0px !important;
    }}

    /* 頂部 Header 驅蟲按鈕樣式 */
    .audio-header-btn button {{
        height: 42px !important;
        min-height: 42px !important;
        font-size: {"1.05rem" if is_senior else "0.85rem"} !important;
        border-radius: 8px !important;
        padding: 4px 8px !important;
        margin-bottom: 0px !important;
    }}

    /* 經典卡片容器 */
    .card {{
        background-color: #FFFFFF;
        border-radius: 12px;
        padding: 18px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.05);
        border-left: 6px solid #2E7D32;
        border-top: 1px solid #E8F5E9;
        border-right: 1px solid #E8F5E9;
        border-bottom: 1px solid #E8F5E9;
        margin-bottom: 16px;
    }}

    /* 氣象數據小方盒 */
    .metric-card {{
        background-color: #F1F8E9;
        border-radius: 10px;
        padding: 10px;
        text-align: center;
        border: 1.5px solid #C5E1A5;
        margin-bottom: 10px;
    }}
    .metric-title {{
        font-size: {"1.05rem" if is_senior else "0.82rem"};
        color: #2E7D32;
        font-weight: bold;
    }}
    .metric-value {{
        font-size: {metric_val_size};
        font-weight: bold;
        color: #1B5E20;
    }}

    /* 標籤 Badges */
    .badge-green {{
        background-color: #2E7D32;
        color: white;
        padding: 4px 10px;
        border-radius: 10px;
        font-size: {"1.05rem" if is_senior else "0.8rem"};
        font-weight: bold;
    }}
    .badge-star {{
        background-color: #E65100;
        color: white;
        padding: 4px 10px;
        border-radius: 10px;
        font-size: {"1.05rem" if is_senior else "0.8rem"};
        font-weight: bold;
    }}
    .badge-sim {{
        background-color: #F57F17;
        color: white;
        padding: 3px 8px;
        border-radius: 8px;
        font-size: {"1.0rem" if is_senior else "0.8rem"};
        font-weight: bold;
    }}
    .badge-feature {{
        background-color: #0277BD;
        color: white;
        padding: 2px 8px;
        border-radius: 6px;
        font-size: {"0.95rem" if is_senior else "0.78rem"};
        font-weight: bold;
        margin-left: 4px;
    }}

    /* 返回按鈕樣式 */
    .back-btn button {{
        background-color: #E8F5E9 !important;
        color: #1B5E20 !important;
        font-weight: bold !important;
        padding: 10px 18px !important;
        font-size: {"1.2rem" if is_senior else "0.95rem"} !important;
        border-radius: 8px !important;
        border: 1.5px solid #C8E6C9 !important;
        margin-bottom: 16px !important;
        height: auto !important;
        min-height: auto !important;
    }}
</style>
""", unsafe_allow_html=True)


# ==================== 3. 澳門氣象實時數據連線 ====================
def update_weather_and_aqi():
    if not st.session_state.override_weather:
        try:
            w_url = "https://api.open-meteo.com/v1/forecast?latitude=22.1987&longitude=113.5439&current=temperature_2m,relative_humidity_2m,precipitation,wind_speed_10m,uv_index"
            res_w = requests.get(w_url, timeout=3)
            if res_w.status_code == 200:
                cur_w = res_w.json().get("current", {})
                st.session_state.global_temp = float(cur_w.get("temperature_2m", 22.5))
                st.session_state.global_uv = float(cur_w.get("uv_index", 1.2))
                st.session_state.global_rain = True if cur_w.get("precipitation", 0) > 0.1 else False
                st.session_state.global_wind = float(cur_w.get("wind_speed_10m", 10.0))

            aq_url = "https://air-quality-api.open-meteo.com/v1/air-quality?latitude=22.1987&longitude=113.5439&current=pm10,pm2_5,us_aqi"
            res_aq = requests.get(aq_url, timeout=3)
            if res_aq.status_code == 200:
                cur_aq = res_aq.json().get("current", {})
                st.session_state.global_pm25 = float(cur_aq.get("pm2_5", 12.0))
                st.session_state.global_pm10 = float(cur_aq.get("pm10", 24.0))
                st.session_state.global_aqi = float(cur_aq.get("us_aqi", 28.0))
        except Exception:
            pass


update_weather_and_aqi()


# ==================== 4. 頂部 Header 與模式切換 ====================
# 長者大字版切換開關
senior_toggle = st.checkbox("👓 **開啟長者大字版**", value=st.session_state.senior_mode)
if senior_toggle != st.session_state.senior_mode:
    st.session_state.senior_mode = senior_toggle
    st.rerun()

audio_badge_text = "🟢 驅蟲運作" if st.session_state.audio_active else "🔴 驅蟲未啟"

col_head1, col_head2, col_head3 = st.columns([1.5, 0.9, 0.9])

with col_head1:
    st.markdown(f"""
    <div>
        <div class="brand-title" style="font-size:{title_base_size}; font-weight:bold; color:#1B5E20;">🍀 絲野仙蹤 Eco-Family</div>
        <div class="brand-sub" style="font-size:{"1.05rem" if is_senior else "0.8rem"}; color:#555;">澳門綠色康旅智慧助手</div>
    </div>
    """, unsafe_allow_html=True)

with col_head2:
    st.markdown('<div class="audio-header-btn">', unsafe_allow_html=True)
    if st.button(f"🔊 {audio_badge_text}", key="top_right_audio_btn"):
        st.session_state.current_page = "audio"
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

with col_head3:
    st.markdown('<div class="sos-header-btn">', unsafe_allow_html=True)
    if st.button("🚨 一鍵求救", key="top_right_sos_btn"):
        st.session_state.current_page = "sos"
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

st.markdown("<hr style='margin-top:5px; margin-bottom:15px; border-color:#E8F5E9;'>", unsafe_allow_html=True)


# ==================== 5. 頁面 1：主選單 ====================
if st.session_state.current_page == "menu":

    if st.button("🗺️ 智慧路線規劃", key="btn_m1", use_container_width=True):
        st.session_state.current_page = "routes"
        st.rerun()

    if st.button("🎒 隨行裝備", key="btn_m2", use_container_width=True):
        st.session_state.current_page = "gear"
        st.rerun()

    ext_url = "https://eddychan912-blip.github.io/eco-tracker11/"
    st.link_button("🔍 生態動植物識別", ext_url, use_container_width=True)


# ==================== 6. 功能頁面 1：🗺️ 智慧路線規劃 ====================
elif st.session_state.current_page == "routes":
    st.markdown('<div class="back-btn">', unsafe_allow_html=True)
    if st.button("← 返回主頁面", key="back_routes"):
        st.session_state.current_page = "menu"
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

    with st.expander("🛠️ 手動氣象模擬"):
        was_override = st.session_state.override_weather
        st.session_state.override_weather = st.checkbox("開啟手動氣象模擬", value=st.session_state.override_weather)
        
        if was_override and not st.session_state.override_weather:
            update_weather_and_aqi()
            st.rerun()

        if st.session_state.override_weather:
            st.session_state.global_temp = st.slider("🌡️ 氣溫 (°C)", 10.0, 38.0, float(st.session_state.global_temp), key="r_temp")
            st.session_state.global_uv = st.slider("☀️ 紫外線 (UV Index)", 0.0, 12.0, float(st.session_state.global_uv), key="r_uv")
            st.session_state.global_pm25 = st.slider("🍃 PM2.5", 5.0, 150.0, float(st.session_state.global_pm25), key="r_pm25")
            st.session_state.global_pm10 = st.slider("🌫️ 懸浮微粒 (PM10)", 10.0, 200.0, float(st.session_state.global_pm10), key="r_pm10")
            st.session_state.global_rain = st.checkbox("🌧️ 是否模擬降雨", value=st.session_state.global_rain, key="r_rain")

    weather_tag_html = '<span class="badge-sim">🛠️ 手動模擬數據中</span>' if st.session_state.override_weather else f'<span style="color:#2E7D32; font-size:{"1.1rem" if is_senior else "0.85rem"}; font-weight:bold;">(📡 澳門實時連線)</span>'
    st.markdown(f"##### ☁️ 澳門當前氣象數據 {weather_tag_html}", unsafe_allow_html=True)

    r1, r2, r3, r4 = st.columns(4)
    with r1:
        st.markdown(f"""<div class="metric-card"><div class="metric-title">🌡️ 氣溫</div><div class="metric-value">{st.session_state.global_temp:.1f}°C</div></div>""", unsafe_allow_html=True)
    with r2:
        st.markdown(f"""<div class="metric-card"><div class="metric-title">☀️ 紫外線</div><div class="metric-value">UV {st.session_state.global_uv:.1f}</div></div>""", unsafe_allow_html=True)
    with r3:
        st.markdown(f"""<div class="metric-card"><div class="metric-title">🍃 PM2.5</div><div class="metric-value">{st.session_state.global_pm25:.1f}</div></div>""", unsafe_allow_html=True)
    with r4:
        rain_text = "是" if st.session_state.global_rain else "否"
        st.markdown(f"""<div class="metric-card"><div class="metric-title">🌧️ 是否降雨</div><div class="metric-value">{rain_text}</div></div>""", unsafe_allow_html=True)

    st.write("")

    st.markdown(f"""
    <div class="card">
        <h3 style="margin-top:0px; color:#1E5631; font-size:{"1.8rem" if is_senior else "1.3rem"};">🗺️ 澳門目的地與路線規劃</h3>
        <p style="font-size:{text_base_size}; margin-bottom:0;">請選擇目的地，系統將依據坡度需求與當前氣候為您推薦最佳路線：</p>
    </div>
    """, unsafe_allow_html=True)

    macau_18_unique_destinations = {
        "大潭山步行徑 (氹仔島)": [
            {
                "id": 101, "target_condition": "rain",
                "name": "🌲 大潭山斜行升降機風雨遮陽主線",
                "shade": 95, "rain_safe": True, "base_crowd": 12,
                "slope": "平緩 (斜行電梯/無障礙)", "has_nursery": True,
                "length": "2.2 公里", "time": "40 分鐘",
                "origin": "113.5615,22.1568", "destination": "113.5630,22.1580", "dest_name": "大潭山斜行升降機",
                "desc": "【下雨/惡劣天氣專屬推薦】設有無障礙風雨連廊與斜行電梯，設有母嬰洗手間，95% 高樹蔭覆蓋。"
            },
            {
                "id": 102, "target_condition": "hot",
                "name": "🦋 大潭山谷地賞蝶樹蔭林陰密徑",
                "shade": 90, "rain_safe": False, "base_crowd": 8,
                "slope": "中等緩坡", "has_nursery": True,
                "length": "1.8 公里", "time": "35 分鐘",
                "origin": "113.5615,22.1568", "destination": "113.5620,22.1595", "dest_name": "大潭山郊野公園",
                "desc": "【高溫/強紫外線專屬推薦】茂密山谷樹蔭天然擋陽，郊野公園內備有母嬰室及休息亭。"
            },
            {
                "id": 103, "target_condition": "cool",
                "name": "☀️ 大潭山山頂瞭望台 360度觀景線",
                "shade": 45, "rain_safe": False, "base_crowd": 28,
                "slope": "陡坡攀升", "has_nursery": False,
                "length": "3.8 公里", "time": "70 分鐘",
                "origin": "113.5615,22.1568", "destination": "113.5650,22.1610", "dest_name": "大潭山觀察台",
                "desc": "【晴朗涼爽專屬推薦】直達山頂瞭望台，視野無遮擋，俯瞰路氹金光大道全景。"
            }
        ],
        "松山 (東望洋) 健康徑 (澳門半島)": [
            {
                "id": 201, "target_condition": "rain",
                "name": "🗼 東望洋燈塔與防空洞展館歷史避雨線",
                "shade": 60, "rain_safe": True, "base_crowd": 30,
                "slope": "平緩道路", "has_nursery": True,
                "length": "2.5 公里", "time": "50 分鐘",
                "origin": "113.5482,22.1965", "destination": "113.5498,22.1968", "dest_name": "東望洋燈塔",
                "desc": "【下雨天氣專屬推薦】途經松山防空洞展館，可隨時入內避雨，展館內設有母嬰設施。"
            },
            {
                "id": 202, "target_condition": "hot",
                "name": "🌿 松山公園高樹蔭綠亭遮陽漫步線",
                "shade": 92, "rain_safe": True, "base_crowd": 20,
                "slope": "平緩道路", "has_nursery": True,
                "length": "1.2 公里", "time": "25 分鐘",
                "origin": "113.5482,22.1965", "destination": "113.5488,22.1972", "dest_name": "松山公園",
                "desc": "【高溫/強紫外線專屬推薦】全線密集高大榕樹掩映，公園洗手間配備母嬰護理台。"
            },
            {
                "id": 203, "target_condition": "cool",
                "name": "🏃‍♂️ 松山環山防滑塑膠跑道親子健身線",
                "shade": 75, "rain_safe": False, "base_crowd": 55,
                "slope": "中等緩坡", "has_nursery": False,
                "length": "1.7 公里", "time": "30 分鐘",
                "origin": "113.5482,22.1965", "destination": "113.5490,22.1980", "dest_name": "松山跑步徑",
                "desc": "【晴朗涼爽專屬推薦】澳門熱門運動步道，設有兒童遊樂場與休閒設施。"
            }
        ],
        "路環黑沙水庫健康徑 (路環島)": [
            {
                "id": 301, "target_condition": "rain",
                "name": "🛶 黑沙水庫水上單車風雨亭線",
                "shade": 70, "rain_safe": True, "base_crowd": 18,
                "slope": "平緩道路", "has_nursery": True,
                "length": "1.0 公里", "time": "25 分鐘",
                "origin": "113.5682,22.1245", "destination": "113.5688,22.1250", "dest_name": "黑沙水庫水上單車",
                "desc": "【下雨天氣專屬推薦】設有大型景觀避雨亭，遊客中心內設有育嬰室設施。"
            },
            {
                "id": 302, "target_condition": "hot",
                "name": "💧 黑沙水庫吊橋環湖高蔭氧吧線",
                "shade": 94, "rain_safe": False, "base_crowd": 10,
                "slope": "中等緩坡", "has_nursery": True,
                "length": "1.5 公里", "time": "35 分鐘",
                "origin": "113.5682,22.1245", "destination": "113.5695,22.1255", "dest_name": "黑沙水庫郊野公園",
                "desc": "【高溫/強紫外線專屬推薦】濃密樹冠覆蓋湖畔步道，公園服務站備有母嬰室。"
            },
            {
                "id": 303, "target_condition": "cool",
                "name": "🌲 水庫後山原生植物科普攬勝線",
                "shade": 60, "rain_safe": False, "base_crowd": 8,
                "slope": "陡坡攀升", "has_nursery": False,
                "length": "2.0 公里", "time": "45 分鐘",
                "origin": "113.5682,22.1245", "destination": "113.5700,22.1260", "dest_name": "黑沙水庫植物園",
                "desc": "【晴朗涼爽專屬推薦】視野良好，沿途標註澳門原生植物科普牌。"
            }
        ],
        "小潭山 2000 環山徑 (氹仔島)": [
            {
                "id": 401, "target_condition": "rain",
                "name": "🌊 小潭山西灣大橋海景風雨涼亭線",
                "shade": 80, "rain_safe": True, "base_crowd": 14,
                "slope": "平緩道路", "has_nursery": True,
                "length": "2.3 公里", "time": "45 分鐘",
                "origin": "113.5435,22.1521", "destination": "113.5445,22.1530", "dest_name": "小潭山2000環山徑",
                "desc": "【下雨天氣專屬推薦】沿途涼亭極多，設有無障礙洗手間及母嬰換尿布台。"
            },
            {
                "id": 402, "target_condition": "hot",
                "name": "👶 小潭山無障礙坡道高蔭林陰線",
                "shade": 91, "rain_safe": True, "base_crowd": 9,
                "slope": "平緩 (無障礙坡道)", "has_nursery": True,
                "length": "1.6 公里", "time": "30 分鐘",
                "origin": "113.5435,22.1521", "destination": "113.5440,22.1528", "dest_name": "小潭山休閒花園",
                "desc": "【高溫/強紫外線專屬推薦】樹蔭極高，坡道平緩，帶嬰兒車極度舒適，設母嬰室。"
            },
            {
                "id": 403, "target_condition": "cool",
                "name": "⛰️ 小潭山山頂天際線視野縱走線",
                "shade": 50, "rain_safe": False, "base_crowd": 22,
                "slope": "陡坡攀升", "has_nursery": False,
                "length": "3.5 公里", "time": "60 分鐘",
                "origin": "113.5435,22.1521", "destination": "113.5460,22.1545", "dest_name": "小潭山山頂觀景點",
                "desc": "【晴朗涼爽專屬推薦】遠眺澳門半島高樓天際線，景致開闊。"
            }
        ],
        "黑沙龍爪角海岸徑 (路環島)": [
            {
                "id": 501, "target_condition": "rain",
                "name": "⛩️ 榕樹灣風雨亭連廊避雨線",
                "shade": 85, "rain_safe": True, "base_crowd": 15,
                "slope": "平緩道路", "has_nursery": False,
                "length": "1.0 公里", "time": "25 分鐘",
                "origin": "113.5712,22.1098", "destination": "113.5718,22.1102", "dest_name": "榕樹灣風雨亭",
                "desc": "【下雨天氣專屬推薦】大榕樹群與涼亭避風避雨，安全性高。"
            },
            {
                "id": 502, "target_condition": "hot",
                "name": "🗿 龍爪角竹灣高蔭避暑步道",
                "shade": 88, "rain_safe": False, "base_crowd": 25,
                "slope": "中等緩坡", "has_nursery": True,
                "length": "1.8 公里", "time": "45 分鐘",
                "origin": "113.5712,22.1098", "destination": "113.5730,22.1120", "dest_name": "竹灣豪園觀景台",
                "desc": "【高溫/強紫外線專屬推薦】竹林與綠樹擋住海面烈日暴曬，起點設有母嬰設施。"
            },
            {
                "id": 503, "target_condition": "cool",
                "name": "🌊 龍爪角奇石聽濤海岸地質線",
                "shade": 30, "rain_safe": False, "base_crowd": 60,
                "slope": "中等緩坡 (部分礁石)", "has_nursery": False,
                "length": "1.2 公里", "time": "40 分鐘",
                "origin": "113.5712,22.1098", "destination": "113.5725,22.1110", "dest_name": "龍爪角海岸徑",
                "desc": "【晴朗涼爽專屬推薦】沿海奇石，聽濤觀海，晴天無浪時極致震撼。"
            }
        ],
        "望廈山市政公園步道 (澳門半島)": [
            {
                "id": 601, "target_condition": "rain",
                "name": "🌺 望廈山溫室展館室內避雨線",
                "shade": 95, "rain_safe": True, "base_crowd": 12,
                "slope": "平緩道路", "has_nursery": True,
                "length": "0.8 公里", "time": "20 分鐘",
                "origin": "113.5488,22.2062", "destination": "113.5490,22.2065", "dest_name": "望廈山溫室展館",
                "desc": "【下雨天氣專屬推薦】室內溫室展示花卉，下雨天不濕身，設有標準母嬰室。"
            },
            {
                "id": 602, "target_condition": "hot",
                "name": "🌿 望廈山茂密綠林避暑步道",
                "shade": 92, "rain_safe": True, "base_crowd": 16,
                "slope": "平緩道路", "has_nursery": True,
                "length": "1.1 公里", "time": "30 分鐘",
                "origin": "113.5488,22.2062", "destination": "113.5495,22.2070", "dest_name": "望廈山市政公園",
                "desc": "【高溫/強紫外線專屬推薦】市區高覆蓋天然綠肺遮陽，公園處備有母嬰育嬰間。"
            },
            {
                "id": 603, "target_condition": "cool",
                "name": "🏃‍♂️ 望廈山砲台古蹟文化攬勝線",
                "shade": 70, "rain_safe": False, "base_crowd": 20,
                "slope": "中等緩坡", "has_nursery": False,
                "length": "1.5 公里", "time": "35 分鐘",
                "origin": "113.5488,22.2062", "destination": "113.5500,22.2075", "dest_name": "望廈砲台",
                "desc": "【晴朗涼爽專屬推薦】澳門歷史文化古蹟步道，展望澳門北區城市景觀。"
            }
        ]
    }

    col_sel1, col_sel2 = st.columns([2, 1])
    with col_sel1:
        selected_dest = st.selectbox("📍 請選擇澳門目的地：", list(macau_18_unique_destinations.keys()))
    with col_sel2:
        selected_slope = st.selectbox("🏔️ 坡度篩選：", ["全部坡度", "平緩 (無障礙/推車友善)", "中等緩坡", "陡坡攀升"])

    need_nursery = st.checkbox("🍼 僅顯示設有母嬰室 / 育嬰設施之路線", value=False)

    cur_temp = st.session_state.global_temp
    cur_uv = st.session_state.global_uv
    is_rain = st.session_state.global_rain

    dest_routes = macau_18_unique_destinations[selected_dest]
    time_seed = int(time.time() / 8)

    if is_rain:
        st.info("🌧️ 檢測到降雨天氣！系統已為您優先推薦【風雨遮陽 / 室內避雨路線】。")
    elif cur_temp >= 26.0 or cur_uv >= 2.5:
        st.info("☀️ 檢測到高溫/強紫外線！系統已為您優先推薦【高樹蔭覆蓋林陰避暑路線】。")
    else:
        st.success("🌤️ 當前天氣晴朗宜人！系統已為您優先推薦【山頂展望 / 景觀視野路線】。")

    filtered_routes = []
    for r in dest_routes:
        if need_nursery and not r["has_nursery"]:
            continue
            
        if selected_slope != "全部坡度":
            if "平緩" in selected_slope and "平緩" not in r["slope"]:
                continue
            elif "中等" in selected_slope and "中等" not in r["slope"]:
                continue
            elif "陡坡" in selected_slope and "陡坡" not in r["slope"]:
                continue

        live_crowd_delta = int(math.sin(time_seed + r["id"]) * 5)
        r["live_crowd"] = max(3, r["base_crowd"] + live_crowd_delta)

        cond = r.get("target_condition", "")
        
        if is_rain:
            score = 98.0 if cond == "rain" else (65.0 if cond == "hot" else 40.0)
        elif cur_temp >= 26.0 or cur_uv >= 2.5:
            score = 98.0 if cond == "hot" else (60.0 if cond == "cool" else 50.0)
        else:
            score = 98.0 if cond == "cool" else (70.0 if cond == "hot" else 55.0)

        r["dynamic_score"] = round(score, 1)
        filtered_routes.append(r)

    sorted_dest_routes = sorted(filtered_routes, key=lambda x: x["dynamic_score"], reverse=True)

    st.markdown(f"#### 🎯 當前推薦路線 ({len(sorted_dest_routes)} 條)：")

    if not sorted_dest_routes:
        st.warning("⚠️ 目前無符合條件之路線，請嘗試放寬篩選條件。")

    for idx, route in enumerate(sorted_dest_routes):
        is_best = (idx == 0)
        badge = '<span class="badge-star">🌟 當前最佳推薦</span>' if is_best else f'<span class="badge-green">適應分: {route["dynamic_score"]}</span>'
        nursery_badge = '<span class="badge-feature">🍼 設母嬰室</span>' if route["has_nursery"] else ''

        nav_url = f"https://uri.amap.com/navigation?from={route['origin']},Start&to={route['destination']},{urllib.parse.quote(route['dest_name'])}&mode=walk&policy=1&src=mypage&callnative=1"

        st.markdown(f"""
        <div class="card" style="{'border-left:6px solid #E65100; background-color:#FFFDE7;' if is_best else ''}">
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">
                <h4 style="margin:0; color:#1B5E20; font-size:{"1.5rem" if is_senior else "1.15rem"};">{route['name']} {nursery_badge}</h4>
                {badge}
            </div>
            <p style="font-size:{text_base_size}; color:#333; margin-bottom:8px;">{route['desc']}</p>
            <div style="font-size:{text_base_size}; color:#222; line-height:1.6; margin-bottom:12px;">
                <b>📏 長度：</b> {route['length']} | <b>⏱️ 時間：</b> {route['time']}<br>
                <b>⛰️ 坡度：</b> <b style="color:#0277BD;">{route['slope']}</b> | <b>🌳 樹蔭：</b> {route['shade']}%
            </div>
            <a href="{nav_url}" target="_blank" style="text-decoration:none;">
                <div style="
                    background-color:#1B5E20; color:white; text-align:center;
                    padding:12px; border-radius:10px; font-weight:bold; font-size:{"1.35rem" if is_senior else "0.95rem"};
                ">
                    🧭 開啟地圖導航
                </div>
            </a>
        </div>
        """, unsafe_allow_html=True)


# ==================== 7. 功能頁面 2：🎒 隨行裝備 ====================
elif st.session_state.current_page == "gear":
    st.markdown('<div class="back-btn">', unsafe_allow_html=True)
    if st.button("← 返回主頁面", key="back_gear"):
        st.session_state.current_page = "menu"
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

    with st.expander("🛠️ 手動氣象模擬"):
        was_override = st.session_state.override_weather
        st.session_state.override_weather = st.checkbox("開啟手動氣象模擬", value=st.session_state.override_weather, key="gear_sim_toggle")
        
        if was_override and not st.session_state.override_weather:
            update_weather_and_aqi()
            st.rerun()

        if st.session_state.override_weather:
            st.session_state.global_temp = st.slider("🌡️ 氣溫 (°C)", 10.0, 38.0, float(st.session_state.global_temp), key="g_temp")
            st.session_state.global_uv = st.slider("☀️ 紫外線 (UV Index)", 0.0, 12.0, float(st.session_state.global_uv), key="g_uv")
            st.session_state.global_pm25 = st.slider("🍃 PM2.5", 5.0, 150.0, float(st.session_state.global_pm25), key="g_pm25")
            st.session_state.global_pm10 = st.slider("🌫️ 懸浮微粒 (PM10)", 10.0, 200.0, float(st.session_state.global_pm10), key="g_pm10")
            st.session_state.global_rain = st.checkbox("🌧️ 是否模擬降雨", value=st.session_state.global_rain, key="g_rain")

    weather_tag_html = '<span class="badge-sim">🛠️ 手動模擬數據中</span>' if st.session_state.override_weather else f'<span style="color:#2E7D32; font-size:{"1.1rem" if is_senior else "0.85rem"}; font-weight:bold;">(📡 澳門實時連線)</span>'
    st.markdown(f"##### ☁️ 澳門當前氣象數據 {weather_tag_html}", unsafe_allow_html=True)

    r1, r2, r3, r4 = st.columns(4)
    with r1:
        st.markdown(f"""<div class="metric-card"><div class="metric-title">🌡️ 氣溫</div><div class="metric-value">{st.session_state.global_temp:.1f}°C</div></div>""", unsafe_allow_html=True)
    with r2:
        st.markdown(f"""<div class="metric-card"><div class="metric-title">☀️ 紫外線</div><div class="metric-value">UV {st.session_state.global_uv:.1f}</div></div>""", unsafe_allow_html=True)
    with r3:
        st.markdown(f"""<div class="metric-card"><div class="metric-title">🍃 PM2.5</div><div class="metric-value">{st.session_state.global_pm25:.1f}</div></div>""", unsafe_allow_html=True)
    with r4:
        rain_text = "是" if st.session_state.global_rain else "否"
        st.markdown(f"""<div class="metric-card"><div class="metric-title">🌧️ 是否降雨</div><div class="metric-value">{rain_text}</div></div>""", unsafe_allow_html=True)

    st.write("")

    st.markdown(f"""
    <div class="card">
        <h3 style="margin-top:0px; color:#1E5631; font-size:{"1.8rem" if is_senior else "1.3rem"};">🎒 當前氣象推薦隨行裝備</h3>
        <p style="font-size:{text_base_size}; margin-bottom:0;">根據氣候精算的推薦清單：</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("##### 📌 出行必備基礎裝備")
    st.checkbox("🍼 **飲用水 / 保溫瓶**", value=True, key="gear_water")
    st.checkbox("🧻 **濕紙巾與個人衛生用品**", value=True, key="gear_wipes")
    st.checkbox("🩹 **隨身 OK 繃與常用藥品**", value=True, key="gear_firstaid")

    if st.session_state.global_rain:
        st.markdown("##### 🌧️ 降雨防護裝備")
        st.checkbox("🌧️ **雨傘與雨衣**", value=True, key="gear_rain1")
        st.checkbox("🌂 **備用替換衣物**", value=True, key="gear_rain2")

    cur_uv = st.session_state.global_uv
    if cur_uv >= 2.5:
        st.markdown(f"##### ☀️ 防曬專屬裝備 (UV {cur_uv:.1f} 偏強)")
        st.checkbox("☀️ **防曬乳 (SPF50+)**", value=True, key="gear_uv_high1")
        st.checkbox("🧢 **遮陽帽與太陽眼鏡**", value=True, key="gear_uv_high2")

    cur_t = st.session_state.global_temp
    if cur_t >= 26.0:
        st.markdown(f"##### 🌡️ 高溫防暑裝備 ({cur_t:.1f}°C 偏熱)")
        st.checkbox("🌬️ **可攜式小風扇**", value=True, key="gear_temp_hot1")
        st.checkbox("🧊 **補充電解質飲品**", value=True, key="gear_temp_hot2")
    elif cur_t <= 20.0:
        st.markdown(f"##### 🧥 保暖防風裝備 ({cur_t:.1f}°C 偏涼)")
        st.checkbox("🧥 **保暖外套**", value=True, key="gear_temp_cold1")

    cur_pm25 = st.session_state.global_pm25
    if cur_pm25 >= 15.0:
        st.markdown(f"##### 😷 呼吸防護裝備 (PM2.5 {cur_pm25:.1f})")
        st.checkbox("😷 **防護口罩**", value=True, key="gear_pm_high")


# ==================== 8. 功能頁面 3：🪰 多頻率驅聲波 ====================
elif st.session_state.current_page == "audio":
    st.markdown('<div class="back-btn">', unsafe_allow_html=True)
    if st.button("← 返回主頁面", key="back_audio"):
        st.session_state.current_page = "menu"
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown(f"""
    <div class="card">
        <h3 style="margin-top:0px; color:#1E5631; font-size:{"1.8rem" if is_senior else "1.3rem"};">🪰 多頻率驅聲波</h3>
        <p style="font-size:{text_base_size}; margin-bottom:0;">選擇昆蟲頻率，啟動後可離頁持續播放。</p>
    </div>
    """, unsafe_allow_html=True)

    freq_options = [
        "17.4 kHz - 模擬雄蚊翅聲 (驅避咬人母蚊)",
        "14.8 kHz - 蠓蟲/小咬 (黑翅蕈蚋) 專用",
        "12.5 kHz - 蜂類與飛蟲 警戒頻率",
        "19.0 kHz - 草叢綜合超聲波 (大人小孩無感)"
    ]

    selected_idx = freq_options.index(st.session_state.selected_insect_freq) if st.session_state.selected_insect_freq in freq_options else 0
    freq_choice = st.radio("🎯 請選擇要驅避的昆蟲種類：", freq_options, index=selected_idx)
    st.session_state.selected_insect_freq = freq_choice

    freq_map = {
        "17.4 kHz - 模擬雄蚊翅聲 (驅避咬人母蚊)": 17400,
        "14.8 kHz - 蠓蟲/小咬 (黑翅蕈蚋) 專用": 14800,
        "12.5 kHz - 蜂類與飛蟲 警戒頻率": 12500,
        "19.0 kHz - 草叢綜合超聲波 (大人小孩無感)": 19000
    }
    current_hz = freq_map[freq_choice]

    st.markdown(f"""
    <div class="card" style="text-align: center;">
        <h2 style="color: #2E7D32; font-size: {"2.8rem" if is_senior else "2.1rem"}; margin:0;">{current_hz / 1000:.1f} kHz</h2>
        <p style="font-size:{text_base_size}; color:#666; margin-top:4px;">模式：<b>{freq_choice.split('-')[1].strip()}</b></p>
    </div>
    """, unsafe_allow_html=True)

    col_a1, col_a2 = st.columns(2)
    with col_a1:
        if st.button("▶️ 啟動發聲", key="btn_start_audio"):
            st.session_state.audio_active = True
            st.toast(f"已啟動 {current_hz/1000:.1f}kHz 超聲波防護！", icon="🔊")
            st.rerun()
    with col_a2:
        if st.button("⏹️ 停止發聲", key="btn_stop_audio"):
            st.session_state.audio_active = False
            st.toast("已關閉超聲波防護。", icon="🛑")
            st.rerun()

    audio_js_template = """
    <div style="text-align:center; padding:10px; background:#F1F8E9; border-radius:10px;">
        <p style="font-size:__STATUS_SIZE__; color:#2E7D32; font-weight:bold; margin:0;">
            __STATUS_TEXT__
        </p>
    </div>
    <script>
        var actx = null;
        var osc = null;
        if (__IS_ACTIVE__) {
            try {
                actx = new (window.AudioContext || window.webkitAudioContext)();
                osc = actx.createOscillator();
                var g = actx.createGain();
                osc.type = 'sine';
                osc.frequency.setValueAtTime(__CURRENT_HZ__, actx.currentTime);
                g.gain.setValueAtTime(0.12, actx.currentTime);
                osc.connect(g);
                g.connect(actx.destination);
                osc.start();
            } catch(e) {}
        }
    </script>
    """
    status_str = "🟢 超聲波持續播放中..." if st.session_state.audio_active else "🔴 聲波目前未啟動"
    audio_js = audio_js_template.replace("__STATUS_TEXT__", status_str)\
                                .replace("__STATUS_SIZE__", "1.3rem" if is_senior else "0.9rem")\
                                .replace("__IS_ACTIVE__", 'true' if st.session_state.audio_active else 'false')\
                                .replace("__CURRENT_HZ__", str(current_hz))

    st.components.v1.html(audio_js, height=85 if is_senior else 75)


# ==================== 9. 功能頁面 4：🚨 一鍵求救專區 ====================
elif st.session_state.current_page == "sos":
    st.markdown('<div class="back-btn">', unsafe_allow_html=True)
    if st.button("← 返回主頁面", key="back_sos"):
        st.session_state.current_page = "menu"
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown(f"""
    <div class="card" style="border-left:6px solid #C62828; background-color:#FFEBEE;">
        <h3 style="margin-top:0px; color:#B71C1C; font-size:{"1.8rem" if is_senior else "1.3rem"};">🚨 一鍵求救與 GPS 通報</h3>
        <p style="font-size:{text_base_size}; color:#C62828; margin-bottom:0;">遇到緊急情況請保持鎮靜，點擊下方按鈕可撥打電話或發送定位訊息：</p>
    </div>
    """, unsafe_allow_html=True)

    sos_js_template = """
    <div style="text-align:center; padding:12px; background-color:#FFEBEE; border-radius:10px; border:2px solid #FFCDD2; margin-bottom:12px;">
        <div id="sosGpsStatus" style="font-size:__STATUS_SIZE__; color:#C62828; font-weight:bold; margin-bottom:6px;">
            📡 正在獲取求救 GPS 座標...
        </div>
        <div id="regionNotice" style="font-size:__NOTICE_SIZE__; color:#B71C1C; font-weight:bold;"></div>
    </div>

    <div style="background-color:#FFFFFF; border-radius:12px; padding:16px; border-left:6px solid #C62828; box-shadow:0 2px 10px rgba(0,0,0,0.05); margin-bottom:16px; text-align:center;">
        <h4 style="color:#C62828; margin-top:0; font-size:__TITLE_SIZE__;">📋 複製求救簡訊內容</h4>
        
        <div style="margin-bottom:12px;">
            <button id="copyBtn" onclick="copySosText()" style="width:100%; background-color:#C62828; color:white; font-size:__BTN_SIZE__; font-weight:bold; padding:16px; border:none; border-radius:12px; cursor:pointer; box-shadow:0 4px 10px rgba(198,40,40,0.3);">
                📋 一鍵複製求救簡訊 (含座標)
            </button>
        </div>

        <p style="font-size:__TEXT_SIZE__; color:#444; text-align:left; margin-bottom:4px; font-weight:bold;">📱 可將內容貼至微信或簡訊發送：</p>
        <textarea id="sosTextarea" readonly style="width:100%; height:120px; background-color:#F9F9F9; border-radius:8px; border:1.5px solid #FFCDD2; padding:10px; font-family:sans-serif; font-size:__TEXT_SIZE__; box-sizing:border-box; color:#222;"></textarea>
    </div>

    <div id="phoneArea" style="margin-bottom:16px;">
        <h5 style="margin-bottom:8px; color:#1B5E20; font-size:__TITLE_SIZE__;">📞 地區求助電話直撥</h5>
        <div style="display:flex; gap:10px;">
            <a id="pBtn1" href="tel:110" style="flex:1; text-decoration:none;">
                <div style="background-color:#C62828; color:white; text-align:center; padding:14px; border-radius:10px; font-weight:bold; font-size:__BTN_SIZE__;">
                    📞 110 報案
                </div>
            </a>
            <a id="pBtn2" href="tel:119" style="flex:1; text-decoration:none;">
                <div style="background-color:#C62828; color:white; text-align:center; padding:14px; border-radius:10px; font-weight:bold; font-size:__BTN_SIZE__;">
                    📞 119 消防
                </div>
            </a>
            <a id="pBtn3" href="tel:120" style="flex:1; text-decoration:none;">
                <div style="background-color:#C62828; color:white; text-align:center; padding:14px; border-radius:10px; font-weight:bold; font-size:__BTN_SIZE__;">
                    📞 120 急救
                </div>
            </a>
        </div>
    </div>

    <script>
        function generateSosText(lat, lon) {
            var nick = "__USER_NICK__";
            return "【🚨 SOS 求救】\\n" +
                   "暱稱：" + nick + "\\n" +
                   "GPS 座標：緯度 " + lat.toFixed(5) + ", 經度 " + lon.toFixed(5) + "\\n" +
                   "地圖位置：https://maps.google.com/?q=" + lat.toFixed(5) + "," + lon.toFixed(5) + "\\n" +
                   "請盡快搜救！";
        }

        function copySosText() {
            var ta = document.getElementById("sosTextarea");
            ta.select();
            ta.setSelectionRange(0, 99999);
            try {
                document.execCommand('copy');
                document.getElementById("copyBtn").innerText = "✅ 複製成功！請至聊天軟體貼上發送";
                document.getElementById("copyBtn").style.backgroundColor = "#2E7D32";
                setTimeout(function(){
                    document.getElementById("copyBtn").innerText = "📋 一鍵複製求救簡訊 (含座標)";
                    document.getElementById("copyBtn").style.backgroundColor = "#C62828";
                }, 3000);
            } catch(e) {
                alert("請手動選擇文字框內容複製。");
            }
        }

        function updateRegionPhone(lat, lon) {
            var isMacau = (lat >= 22.10 && lat <= 22.22 && lon >= 113.50 && lon <= 113.60);
            var isHK = (lat >= 22.15 && lat <= 22.58 && lon >= 113.80 && lon <= 114.40);

            if (isMacau) {
                document.getElementById("regionNotice").innerHTML = "📍 當前在【澳門地區】，推薦優先撥打 999 或 110/119";
                document.getElementById("pBtn1").href = "tel:999";
                document.getElementById("pBtn1").children[0].innerText = "📞 999 報案";
                document.getElementById("pBtn1").children[0].style.backgroundColor = "#0277BD";
            } else if (isHK) {
                document.getElementById("regionNotice").innerHTML = "📍 當前在【香港地區】，推薦優先撥打 999";
                document.getElementById("pBtn1").href = "tel:999";
                document.getElementById("pBtn1").children[0].innerText = "📞 999 香港求助";
                document.getElementById("pBtn1").children[0].style.backgroundColor = "#0277BD";
            } else {
                document.getElementById("regionNotice").innerHTML = "📍 緊急熱線：110 (公安) / 119 (消防) / 120 (醫療)";
            }
        }

        if (navigator.geolocation) {
            navigator.geolocation.getCurrentPosition(function(position) {
                var lat = position.coords.latitude;
                var lon = position.coords.longitude;
                var accuracy = Math.round(position.coords.accuracy);
                
                document.getElementById("sosGpsStatus").innerHTML = "✅ 已鎖定 GPS 座標 (誤差 ±" + accuracy + "米)";
                
                var txt = generateSosText(lat, lon);
                document.getElementById("sosTextarea").value = txt;
                updateRegionPhone(lat, lon);
            }, function(error) {
                document.getElementById("sosGpsStatus").innerHTML = "⚠️ 請允許定位權限以取得求救座標";
            }, {
                enableHighAccuracy: true,
                maximumAge: 0,
                timeout: 8000
            });
        }
    </script>
    """
xc
    nick_name = st.session_state.user_nickname if st.session_state.user_nickname else "遊客"
    rendered_sos_html = sos_js_template.replace("__USER_NICK__", str(nick_name))\
                                       .replace("__STATUS_SIZE__", "1.3rem" if is_senior else "0.9rem")\
                                       .replace("__NOTICE_SIZE__", "1.1rem" if is_senior else "0.85rem")\
                                       .replace("__TITLE_SIZE__", "1.4rem" if is_senior else "1.05rem")\
                                       .replace("__BTN_SIZE__", "1.35rem" if is_senior else "1.0rem")\
                                       .replace("__TEXT_SIZE__", "1.15rem" if is_senior else "0.85rem")

    st.components.v1.html(rendered_sos_html, height=420 if is_senior else 360)

    st.info("💡 提示：點擊「一鍵複製」按鈕後，可至通訊軟體貼上經緯度文字發送給救援人員！")