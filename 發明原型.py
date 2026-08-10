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
import json
from datetime import datetime

# ==================== 0. 全域跨 Session 共享記憶體 ====================
@st.cache_resource
def get_global_shared_store():
    return {
        "rooms": {},       # { room_id: { nickname: { "time": str, "lat": float, "lon": float, "status": str } } }
        "broadcasts": {}   # { room_id: [ { "sender": str, "msg": str, "time": str } ] }
    }

shared_store = get_global_shared_store()


# Haversine 球面大圓距離真實計算函數 (回傳公尺或公里)
def calculate_haversine(lat1, lon1, lat2, lon2):
    R = 6371000.0  # 地球平均半徑 (公尺)
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = math.sin(delta_phi / 2.0)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0)**2
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    meters = R * c

    if meters < 1000.0:
        return f"{round(meters, 1)} 公尺"
    else:
        return f"{round(meters / 1000.0, 2)} 公里"


# ==================== 1. 全域 Session State 安全初始化 ====================
query_params = st.query_params

if "page" in query_params and query_params["page"]:
    st.session_state.current_page = query_params["page"]

if "joined" in query_params and query_params["joined"] == "1":
    st.session_state.joined_room = True

if "room" in query_params and query_params["room"]:
    st.session_state.room_id = query_params["room"]

if "user" in query_params and query_params["user"]:
    st.session_state.user_nickname = query_params["user"]

# 讀取真實 GPS 座標
if "lat" in query_params and "lon" in query_params:
    try:
        st.session_state.my_lat = float(query_params["lat"])
        st.session_state.my_lon = float(query_params["lon"])
    except ValueError:
        pass

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

# 共享定位房間與暱稱 (預設為空字串，未填寫前不自動進入房間)
if "room_id" not in st.session_state:
    st.session_state.room_id = ""
if "user_nickname" not in st.session_state:
    st.session_state.user_nickname = ""
if "joined_room" not in st.session_state:
    st.session_state.joined_room = False

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

# ==================== 2. 全局 CSS 樣式美化 ====================
st.markdown("""
<style>
    .stApp {
        background-color: #F7FAF8;
        color: #2C3E50;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
    }
    
    /* 隱藏原生側邊欄 */
    section[data-testid="stSidebar"] {
        display: none;
    }

    /* 四大功能按鈕容器寬度與邊距強制對齊 */
    div[data-testid="stButton"], div[data-testid="stLinkButton"] {
        width: 100% !important;
        margin: 0 0 16px 0 !important;
        padding: 0 !important;
        box-sizing: border-box !important;
    }

    /* 四大功能按鈕 100% 強制像素級長度、高度與樣式完全對齊 */
    div[data-testid="stButton"] > button, div[data-testid="stLinkButton"] > a {
        width: 100% !important;
        background-color: #FFFFFF !important;
        color: #1B5E20 !important;
        border-radius: 16px !important;
        height: 76px !important;
        min-height: 76px !important;
        max-height: 76px !important;
        box-shadow: 0 4px 15px rgba(0,0,0,0.04) !important;
        border: 1.5px solid #E8F5E9 !important;
        text-align: center !important;
        font-size: 1.35rem !important;
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
    }

    div[data-testid="stButton"] > button:hover, div[data-testid="stLinkButton"] > a:hover {
        border-color: #2E7D32 !important;
        box-shadow: 0 6px 20px rgba(46,125,50,0.18) !important;
        background-color: #F1F8E9 !important;
        transform: translateY(-2px) !important;
        color: #1B5E20 !important;
        text-decoration: none !important;
    }

    /* 頂部 Header 求救按鈕特化樣式 */
    .sos-header-btn button {
        background-color: #FFEBEE !important;
        color: #C62828 !important;
        border: 1.5px solid #FFCDD2 !important;
        font-weight: 800 !important;
        height: 38px !important;
        min-height: 38px !important;
        font-size: 0.85rem !important;
        border-radius: 8px !important;
        padding: 4px 8px !important;
        margin-bottom: 0px !important;
    }

    /* 頂部 Header 驅蟲按鈕樣式 */
    .audio-header-btn button {
        height: 38px !important;
        min-height: 38px !important;
        font-size: 0.85rem !important;
        border-radius: 8px !important;
        padding: 4px 8px !important;
        margin-bottom: 0px !important;
    }

    /* 經典卡片容器 */
    .card {
        background-color: #FFFFFF;
        border-radius: 12px;
        padding: 18px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.04);
        border-left: 5px solid #2E7D32;
        border-top: 1px solid #E8F5E9;
        border-right: 1px solid #E8F5E9;
        border-bottom: 1px solid #E8F5E9;
        margin-bottom: 16px;
    }

    /* 氣象數據小方盒 */
    .metric-card {
        background-color: #F1F8E9;
        border-radius: 10px;
        padding: 10px;
        text-align: center;
        border: 1px solid #C5E1A5;
        margin-bottom: 10px;
    }
    .metric-title {
        font-size: 0.82rem;
        color: #388E3C;
        font-weight: bold;
    }
    .metric-value {
        font-size: 1.35rem;
        font-weight: bold;
        color: #1B5E20;
    }

    /* 標籤 Badges */
    .badge-green {
        background-color: #2E7D32;
        color: white;
        padding: 4px 10px;
        border-radius: 10px;
        font-size: 0.8rem;
        font-weight: bold;
    }
    .badge-star {
        background-color: #E65100;
        color: white;
        padding: 4px 10px;
        border-radius: 10px;
        font-size: 0.8rem;
        font-weight: bold;
    }
    .badge-sim {
        background-color: #F57F17;
        color: white;
        padding: 3px 8px;
        border-radius: 8px;
        font-size: 0.8rem;
        font-weight: bold;
    }

    /* 返回按鈕樣式 */
    .back-btn button {
        background-color: #E8F5E9 !important;
        color: #1B5E20 !important;
        font-weight: bold !important;
        padding: 8px 16px !important;
        font-size: 0.95rem !important;
        border-radius: 8px !important;
        border: 1px solid #C8E6C9 !important;
        margin-bottom: 16px !important;
        height: auto !important;
        min-height: auto !important;
    }
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


# ==================== 4. 頂部 Header ====================
audio_badge_text = "🟢 驅蟲運作" if st.session_state.audio_active else "🔴 驅蟲未啟"

col_head1, col_head2, col_head3 = st.columns([1.5, 0.9, 0.9])

with col_head1:
    st.markdown("""
    <div>
        <div class="brand-title" style="font-size:1.55rem;">🍀 絲野仙蹤 Eco-Family</div>
        <div class="brand-sub">澳門親子綠色呼吸智慧隨行助手</div>
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
    if st.button("🚨 全國 SOS", key="top_right_sos_btn"):
        st.session_state.current_page = "sos"
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

st.markdown("<hr style='margin-top:5px; margin-bottom:15px; border-color:#E8F5E9;'>", unsafe_allow_html=True)


# ==================== 5. 頁面 1：主選單 ====================
if st.session_state.current_page == "menu":

    if st.button("🗺️ 智慧路線規劃", key="btn_m1", use_container_width=True):
        st.session_state.current_page = "routes"
        st.rerun()

    if st.button("📍 親友共享定位雷達", key="btn_m2", use_container_width=True):
        st.session_state.current_page = "family"
        st.rerun()

    if st.button("🎒 隨行裝備", key="btn_m3", use_container_width=True):
        st.session_state.current_page = "gear"
        st.rerun()

    ext_url = "https://eddychan912-blip.github.io/eco-tracker11/"
    st.link_button("🔍 親子生態動植物識別", ext_url, use_container_width=True)


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

    weather_tag_html = '<span class="badge-sim">🛠️ 手動模擬數據中</span>' if st.session_state.override_weather else '<span style="color:#2E7D32; font-size:0.85rem; font-weight:bold;">(📡 澳門實時連線)</span>'
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

    st.markdown("""
    <div class="card">
        <h3 style="margin-top:0px; color:#1E5631;">🗺️ 澳門目的地與氣象適應路線規劃</h3>
        <p style="font-size:0.9rem; margin-bottom:0;">選擇澳門目的地，系統將依據<b>當前氣溫、紫外線與是否降雨</b>推薦最適路線：</p>
    </div>
    """, unsafe_allow_html=True)

    macau_18_unique_destinations = {
        "大潭山步行徑 (氹仔島)": [
            {
                "id": 101, "target_condition": "rain",
                "name": "🌲 大潭山斜行升降機風雨遮陽主線",
                "shade": 95, "rain_safe": True, "base_crowd": 12,
                "length": "2.2 公里", "time": "40 分鐘",
                "origin": "113.5615,22.1568", "destination": "113.5630,22.1580", "dest_name": "大潭山斜行升降機",
                "desc": "【下雨/惡劣天氣專屬推薦】設有無障礙風雨連廊與斜行電梯，95% 高樹蔭覆蓋防雨防曬。"
            },
            {
                "id": 102, "target_condition": "hot",
                "name": "🦋 大潭山谷地賞蝶樹蔭林陰密徑",
                "shade": 90, "rain_safe": False, "base_crowd": 8,
                "length": "1.8 公里", "time": "35 分鐘",
                "origin": "113.5615,22.1568", "destination": "113.5620,22.1595", "dest_name": "大潭山郊野公園",
                "desc": "【高溫/強紫外線專屬推薦】茂密山谷樹蔭天然擋陽，空氣高負離子降溫。"
            },
            {
                "id": 103, "target_condition": "cool",
                "name": "☀️ 大潭山山頂瞭望台 360度觀景線",
                "shade": 45, "rain_safe": False, "base_crowd": 28,
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
                "length": "2.5 公里", "time": "50 分鐘",
                "origin": "113.5482,22.1965", "destination": "113.5498,22.1968", "dest_name": "東望洋燈塔",
                "desc": "【下雨天氣專屬推薦】途經松山防空洞展館，可隨時入內避雨參觀。"
            },
            {
                "id": 202, "target_condition": "hot",
                "name": "🌿 松山公園高樹蔭綠亭遮陽漫步線",
                "shade": 92, "rain_safe": True, "base_crowd": 20,
                "length": "1.2 公里", "time": "25 分鐘",
                "origin": "113.5482,22.1965", "destination": "113.5488,22.1972", "dest_name": "松山公園",
                "desc": "【高溫/強紫外線專屬推薦】全線密集高大榕樹掩映，涼亭多且設有歇腳茶座。"
            },
            {
                "id": 203, "target_condition": "cool",
                "name": "🏃‍♂️ 松山環山防滑塑膠跑道親子健身線",
                "shade": 75, "rain_safe": False, "base_crowd": 55,
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
                "length": "1.0 公里", "time": "25 分鐘",
                "origin": "113.5682,22.1245", "destination": "113.5688,22.1250", "dest_name": "黑沙水庫水上單車",
                "desc": "【下雨天氣專屬推薦】設有大型景觀避雨亭與無障礙連廊設施。"
            },
            {
                "id": 302, "target_condition": "hot",
                "name": "💧 黑沙水庫吊橋環湖高蔭氧吧線",
                "shade": 94, "rain_safe": False, "base_crowd": 10,
                "length": "1.5 公里", "time": "35 分鐘",
                "origin": "113.5682,22.1245", "destination": "113.5695,22.1255", "dest_name": "黑沙水庫郊野公園",
                "desc": "【高溫/強紫外線專屬推薦】濃密樹冠覆蓋湖畔步道，涼爽宜人。"
            },
            {
                "id": 303, "target_condition": "cool",
                "name": "🌲 水庫後山原生植物科普攬勝線",
                "shade": 60, "rain_safe": False, "base_crowd": 8,
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
                "length": "2.3 公里", "time": "45 分鐘",
                "origin": "113.5435,22.1521", "destination": "113.5445,22.1530", "dest_name": "小潭山2000環山徑",
                "desc": "【下雨天氣專屬推薦】沿途涼亭與防雨歇腳點極多，雨天行走無憂。"
            },
            {
                "id": 402, "target_condition": "hot",
                "name": "👶 小潭山無障礙坡道高蔭林陰線",
                "shade": 91, "rain_safe": True, "base_crowd": 9,
                "length": "1.6 公里", "time": "30 分鐘",
                "origin": "113.5435,22.1521", "destination": "113.5440,22.1528", "dest_name": "小潭山休閒花園",
                "desc": "【高溫/強紫外線專屬推薦】樹蔭極高，坡道平緩，帶嬰兒車極度舒適。"
            },
            {
                "id": 403, "target_condition": "cool",
                "name": "⛰️ 小潭山山頂天際線視野縱走線",
                "shade": 50, "rain_safe": False, "base_crowd": 22,
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
                "length": "1.0 公里", "time": "25 分鐘",
                "origin": "113.5712,22.1098", "destination": "113.5718,22.1102", "dest_name": "榕樹灣風雨亭",
                "desc": "【下雨天氣專屬推薦】大榕樹群與涼亭避風避雨，安全性高。"
            },
            {
                "id": 502, "target_condition": "hot",
                "name": "🗿 龍爪角竹灣高蔭避暑步道",
                "shade": 88, "rain_safe": False, "base_crowd": 25,
                "length": "1.8 公里", "time": "45 分鐘",
                "origin": "113.5712,22.1098", "destination": "113.5730,22.1120", "dest_name": "竹灣豪園觀景台",
                "desc": "【高溫/強紫外線專屬推薦】竹林與綠樹擋住海面烈日暴曬。"
            },
            {
                "id": 503, "target_condition": "cool",
                "name": "🌊 龍爪角奇石聽濤海岸地質線",
                "shade": 30, "rain_safe": False, "base_crowd": 60,
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
                "length": "0.8 公里", "time": "20 分鐘",
                "origin": "113.5488,22.2062", "destination": "113.5490,22.2065", "dest_name": "望廈山溫室展館",
                "desc": "【下雨天氣專屬推薦】室內溫室展示花卉，下雨天完全不濕身。"
            },
            {
                "id": 602, "target_condition": "hot",
                "name": "🌿 望廈山茂密綠林避暑步道",
                "shade": 92, "rain_safe": True, "base_crowd": 16,
                "length": "1.1 公里", "time": "30 分鐘",
                "origin": "113.5488,22.2062", "destination": "113.5495,22.2070", "dest_name": "望廈山市政公園",
                "desc": "【高溫/強紫外線專屬推薦】市區高覆蓋天然綠肺遮陽。"
            },
            {
                "id": 603, "target_condition": "cool",
                "name": "🏃‍♂️ 松山環山防滑塑膠跑道親子健身線",
                "shade": 75, "rain_safe": False, "base_crowd": 55,
                "length": "1.7 公里", "time": "30 分鐘",
                "origin": "113.5482,22.1965", "destination": "113.5490,22.1980", "dest_name": "松山跑步徑",
                "desc": "【晴朗涼爽專屬推薦】澳門熱門運動步道，設有兒童遊樂場與休閒設施。"
            }
        ]
    }

    selected_dest = st.selectbox("📍 請選擇澳門目的地：", list(macau_18_unique_destinations.keys()))

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

    for r in dest_routes:
        live_crowd_delta = int(math.sin(time_seed + r["id"]) * 5)
        r["live_crowd"] = max(3, r["base_crowd"] + live_crowd_delta)

        cond = r.get("target_condition", "")
        
        if is_rain:
            if cond == "rain":
                score = 98.0
            elif cond == "hot":
                score = 65.0
            else:
                score = 40.0
        elif cur_temp >= 26.0 or cur_uv >= 2.5:
            if cond == "hot":
                score = 98.0
            elif cond == "cool":
                score = 60.0
            else:
                score = 50.0
        else:
            if cond == "cool":
                score = 98.0
            elif cond == "hot":
                score = 70.0
            else:
                score = 55.0

        r["dynamic_score"] = round(score, 1)

    sorted_dest_routes = sorted(dest_routes, key=lambda x: x["dynamic_score"], reverse=True)

    st.markdown(f"#### 🎯 當前氣象 (氣溫 {cur_temp:.1f}°C / UV {cur_uv:.1f} / 是否降雨：{'是' if is_rain else '否'}) 推薦路線：")

    for idx, route in enumerate(sorted_dest_routes):
        is_best = (idx == 0)
        badge = '<span class="badge-star">🌟 當前天氣最佳推薦</span>' if is_best else f'<span class="badge-green">適應分: {route["dynamic_score"]}</span>'

        nav_url = f"https://uri.amap.com/navigation?from={route['origin']},Start&to={route['destination']},{urllib.parse.quote(route['dest_name'])}&mode=walk&policy=1&src=mypage&callnative=1"

        st.markdown(f"""
        <div class="card" style="{'border-left:6px solid #E65100; background-color:#FFFDE7;' if is_best else ''}">
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:6px;">
                <h4 style="margin:0; color:#1B5E20; font-size:1.15rem;">{route['name']}</h4>
                {badge}
            </div>
            <p style="font-size:0.88rem; color:#555; margin-bottom:8px;">{route['desc']}</p>
            <div style="font-size:0.83rem; color:#333; line-height:1.6; margin-bottom:12px;">
                <b>📏 長度：</b> {route['length']} | <b>⏱️ 時間：</b> {route['time']} | <b>🌳 樹蔭：</b> {route['shade']}%<br>
                <b>🚶‍♂️ 實時人數：</b> <b style="color:#EF6C00;">{route['live_crowd']} 人</b>
            </div>
            <a href="{nav_url}" target="_blank" style="text-decoration:none;">
                <div style="
                    background-color:#1B5E20; color:white; text-align:center;
                    padding:10px; border-radius:8px; font-weight:bold; font-size:0.95rem;
                ">
                    🧭 開啟路線地圖導航
                </div>
            </a>
        </div>
        """, unsafe_allow_html=True)


# ==================== 7. 功能頁面 2：📍 親友共享定位雷達 ====================
elif st.session_state.current_page == "family":
    st.markdown('<div class="back-btn">', unsafe_allow_html=True)
    if st.button("← 返回主頁面", key="back_family"):
        st.session_state.current_page = "menu"
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("""
    <div class="card">
        <h3 style="margin-top:0px; color:#1E5631;">📍 親友共享定位雷達</h3>
        <p style="font-size:0.9rem; margin-bottom:8px;">請輸入您的暱稱與房間號碼。按下<b>「進入共享房間」</b>後，系統將讀取真實 GPS 定位。<b style="color:#D32F2F;">🔴 紅色為你自己</b>，<b style="color:#1976D2;">🔵 藍色為親友成員</b>。</p>
    </div>
    """, unsafe_allow_html=True)

    col_input1, col_input2 = st.columns(2)
    with col_input1:
        input_nick = st.text_input("👤 您的暱稱 (請填寫)", value=st.session_state.user_nickname, placeholder="例如: 媽媽")
    with col_input2:
        input_room = st.text_input("🔑 房間號碼 (請填寫)", value=st.session_state.room_id, placeholder="例如: 8888")

    btn_col1, btn_col2 = st.columns([2, 1])
    with btn_col1:
        if st.button("🚀 進入共享房間", key="join_room_btn"):
            if not input_nick.strip() or not input_room.strip():
                st.warning("⚠️ 請務必填寫【暱稱】與【房間號碼】後再點擊進入！")
            else:
                st.session_state.user_nickname = input_nick.strip()
                st.session_state.room_id = input_room.strip()
                st.session_state.joined_room = True
                st.rerun()
    
    with btn_col2:
        if st.session_state.joined_room:
            if st.button("🚪 離開房間", key="leave_room_btn"):
                st.session_state.joined_room = False
                st.rerun()

    if not st.session_state.joined_room:
        st.info("💡 請在上方輸入您的 **暱稱** 與 **房間號碼**，並點擊 **「🚀 進入共享房間」** 按鈕以開始雷達定位與成員共享。")
    else:
        room_key = st.session_state.room_id
        current_nickname = st.session_state.user_nickname
        now_time_str = datetime.now().strftime("%H:%M:%S")

        if room_key not in shared_store["rooms"]:
            shared_store["rooms"][room_key] = {}
        if room_key not in shared_store["broadcasts"]:
            shared_store["broadcasts"][room_key] = []

        recent_broadcasts = shared_store["broadcasts"][room_key]
        if recent_broadcasts:
            last_bc = recent_broadcasts[-1]
            st.error(f"🚨 **【緊急集合廣播通知】** 來自成員 **[{last_bc['sender']}]** ({last_bc['time']})：\n\n📢 *\"{last_bc['msg']}\"*")

        shared_store["rooms"][room_key][current_nickname] = {
            "time": now_time_str,
            "lat": st.session_state.my_lat,
            "lon": st.session_state.my_lon,
            "status": "🟢 長亮連線中"
        }

        members = shared_store["rooms"][room_key]
        display_m = []
        
        my_lat = st.session_state.my_lat
        my_lon = st.session_state.my_lon

        member_list_sorted = list(members.items())
        member_js_data = []

        for idx, (nick, info) in enumerate(member_list_sorted):
            is_me = (nick == current_nickname)
            m_lat = info.get("lat", 22.1568)
            m_lon = info.get("lon", 113.5615)

            if is_me:
                dist_str = "0 公尺"
            else:
                dist_str = calculate_haversine(my_lat, my_lon, m_lat, m_lon)

            display_m.append({
                "成員暱稱": f"{nick} (我自己)" if is_me else nick,
                "最後連線時間": info["time"],
                "相對距離 (離我多遠)": dist_str,
                "連線狀態": info["status"]
            })

            color = '#D32F2F' if is_me else '#1976D2'
            display_label = f"{nick} (我自己)" if is_me else nick

            member_js_data.append({
                "nick": display_label,
                "is_me": is_me,
                "lat": m_lat,
                "lon": m_lon,
                "color": color,
                "time": info["time"],
                "dist": dist_str
            })

        member_data_json_str = json.dumps(member_js_data, ensure_ascii=False)

        map_html_template = """
        <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
        <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
        <style>
            .member-label {
                background-color: rgba(255, 255, 255, 0.98) !important;
                border: 1.5px solid #D32F2F !important;
                color: #D32F2F !important;
                font-weight: bold !important;
                font-size: 0.85rem !important;
                border-radius: 6px !important;
                padding: 3px 8px !important;
                box-shadow: 0 2px 6px rgba(0,0,0,0.2) !important;
                white-space: nowrap !important;
            }
            .other-member-label {
                border-color: #1976D2 !important;
                color: #1976D2 !important;
            }
        </style>
        <div style="text-align:center; padding:8px; background-color:#E8F5E9; border-radius:10px; border:1px solid #C8E6C9; margin-bottom:10px;">
            <div id="gpsStatus" style="font-size:0.9rem; color:#1B5E20; font-weight:bold;">
                🔴 紅色：我自己 | 🔵 藍色：親友成員 (已進入房間 [__ROOM_KEY__])
            </div>
        </div>
        <div id="radarMap" style="width: 100%; height: 350px; border-radius: 12px; border: 1.5px solid #C8E6C9;"></div>
        <script>
            var members = __MEMBER_JSON__;
            var map = L.map('radarMap', { preferCanvas: false }).setView([__MY_LAT__, __MY_LON__], 17);
            L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
                maxZoom: 19,
                attribution: '© OpenStreetMap'
            }).addTo(map);

            var myCircleMarker = null;

            members.forEach(function(m) {
                var circle = L.circleMarker([m.lat, m.lon], {
                    color: '#FFFFFF',
                    weight: 2.5,
                    fillColor: m.color,
                    fillOpacity: 0.92,
                    radius: 12
                }).addTo(map);

                var labelClass = m.is_me ? 'member-label' : 'member-label other-member-label';

                circle.bindTooltip('<b>' + m.nick + '</b>', {
                    permanent: true,
                    direction: 'top',
                    className: labelClass,
                    offset: [0, -10]
                }).openTooltip();

                circle.bindPopup('<b>' + m.nick + '</b><br>連線時間: ' + m.time + '<br>相對距離: ' + m.dist);

                if (m.is_me) {
                    myCircleMarker = circle;
                }
            });

            if (navigator.geolocation) {
                navigator.geolocation.watchPosition(function(position) {
                    var lat = position.coords.latitude;
                    var lon = position.coords.longitude;
                    var accuracy = Math.round(position.coords.accuracy);

                    document.getElementById("gpsStatus").innerHTML = "🔴 紅色：我自己 | 🔵 藍色：親友成員 (衛星 GPS 追蹤 ±" + accuracy + "米)";

                    if (myCircleMarker) {
                        myCircleMarker.setLatLng([lat, lon]);
                    }
                }, function(error) {}, {
                    enableHighAccuracy: true,
                    maximumAge: 0,
                    timeout: 10000
                });
            }
        </script>
        """

        integrated_map_html = map_html_template.replace("__ROOM_KEY__", str(room_key))\
                                                .replace("__MEMBER_JSON__", member_data_json_str)\
                                                .replace("__MY_LAT__", str(my_lat))\
                                                .replace("__MY_LON__", str(my_lon))\
                                                .replace("__CURRENT_NICK__", str(current_nickname))

        st.components.v1.html(integrated_map_html, height=425)

        st.markdown(f"#### 📡 房間 **[{room_key}]** 實時成員清單 ({len(display_m)} 人)：")
        df_m = pd.DataFrame(display_m)
        st.dataframe(df_m, use_container_width=True)

        col_b1, col_b2 = st.columns(2)
        with col_b1:
            if st.button("📢 發送集合通知", key="send_bc"):
                shared_store["broadcasts"][room_key].append({
                    "sender": current_nickname,
                    "msg": f"注意！成員 [{current_nickname}] 發起了緊急集合通知，請儘快至附近地標會合！",
                    "time": now_time_str
                })
                st.toast("已發送集合通知！已寫入共享廣播頻道。", icon="📢")
                st.rerun()
        with col_b2:
            if st.button("🔄 重新整理雷達連線", key="ref_radar"):
                st.rerun()


# ==================== 8. 功能頁面 3：🎒 隨行裝備 ====================
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

    weather_tag_html = '<span class="badge-sim">🛠️ 手動模擬數據中</span>' if st.session_state.override_weather else '<span style="color:#2E7D32; font-size:0.85rem; font-weight:bold;">(📡 澳門實時連線)</span>'
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

    st.markdown("""
    <div class="card">
        <h3 style="margin-top:0px; color:#1E5631;">🎒 當前氣象動態推薦隨行裝備</h3>
        <p style="font-size:0.9rem; margin-bottom:0;">系統根據目前的<b>氣溫、紫外線、是否降雨與懸浮微粒</b>數據精算出的推薦清單：</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("##### 📌 出行必備基礎裝備")
    st.checkbox("🍼 **兒童水壺 / 保溫杯** (隨時補充水分)", value=True, key="gear_water")
    st.checkbox("🧻 **濕紙巾與消毒個人用品**", value=True, key="gear_wipes")
    st.checkbox("🩹 **隨身創可貼與急救盒**", value=True, key="gear_firstaid")

    if st.session_state.global_rain:
        st.markdown("##### 🌧️ 是否降雨：當前降雨專屬裝備")
        st.checkbox("🌧️ **嬰兒車透氣防雨罩 & 親子大雨傘**", value=True, key="gear_rain1")
        st.checkbox("🌂 **備用寶寶乾爽衣物 1 套 (防水袋裝)**", value=True, key="gear_rain2")
        st.checkbox("👟 **兒童防滑雨鞋**", value=True, key="gear_rain3")

    cur_uv = st.session_state.global_uv
    if cur_uv >= 2.5:
        st.markdown(f"##### ☀️ 防曬護膚專屬裝備 (當前 UV {cur_uv:.1f} 偏強)")
        st.checkbox("☀️ **兒童高效防曬乳 (SPF50+)**", value=True, key="gear_uv_high1")
        st.checkbox("🧢 **推車抗 UV 遮陽罩 & 親子大簷太陽帽**", value=True, key="gear_uv_high2")
        st.checkbox("🕶️ **兒童太陽眼鏡**", value=True, key="gear_uv_high3")

    cur_t = st.session_state.global_temp
    if cur_t >= 26.0:
        st.markdown(f"##### 🌡️ 高溫防暑專屬裝備 (當前 {cur_t:.1f}°C 偏熱)")
        st.checkbox("🌬️ **夾式推車靜音小風扇** *(防止寶寶高溫中暑)*", value=True, key="gear_temp_hot1")
        st.checkbox("🧊 **兒童退熱貼 / 電解質水補給包**", value=True, key="gear_temp_hot2")
    elif cur_t <= 20.0:
        st.markdown(f"##### 🧥 保暖防風專屬裝備 (當前 {cur_t:.1f}°C 偏涼)")
        st.checkbox("🧥 **兒童保暖防風外套 & 小毛毯**", value=True, key="gear_temp_cold1")
        st.checkbox("☕ **熱水保溫壺**", value=True, key="gear_temp_cold2")

    cur_pm25 = st.session_state.global_pm25
    if cur_pm25 >= 15.0:
        st.markdown(f"##### 😷 懸浮微粒：呼吸道護理裝備 (當前 PM2.5 {cur_pm25:.1f})")
        st.checkbox("😷 **兒童高防護透氣口罩**", value=True, key="gear_pm_high")


# ==================== 9. 功能頁面 4：🪰 多頻率驅聲波 ====================
elif st.session_state.current_page == "audio":
    st.markdown('<div class="back-btn">', unsafe_allow_html=True)
    if st.button("← 返回主頁面", key="back_audio"):
        st.session_state.current_page = "menu"
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("""
    <div class="card">
        <h3 style="margin-top:0px; color:#1E5631;">🪰 多頻率驅蚊驅蟲器</h3>
        <p style="font-size:0.9rem; margin-bottom:0;">選擇特定昆蟲頻率，啟動後離開此頁面聲波依然保持播放。</p>
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
        <h2 style="color: #2E7D32; font-size: 2.1rem; margin:0;">{current_hz / 1000:.1f} kHz</h2>
        <p style="font-size:0.85rem; color:#666; margin-top:4px;">選擇頻率：<b>{freq_choice.split('-')[1].strip()}</b></p>
    </div>
    """, unsafe_allow_html=True)

    col_a1, col_a2 = st.columns(2)
    with col_a1:
        if st.button("▶️ 啟動驅聲波防護", key="btn_start_audio"):
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
        <p style="font-size:0.9rem; color:#2E7D32; font-weight:bold; margin:0;">
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
    status_str = "🟢 超聲波背景持續播放中..." if st.session_state.audio_active else "🔴 聲波目前未啟動"
    audio_js = audio_js_template.replace("__STATUS_TEXT__", status_str)\
                                .replace("__IS_ACTIVE__", 'true' if st.session_state.audio_active else 'false')\
                                .replace("__CURRENT_HZ__", str(current_hz))

    st.components.v1.html(audio_js, height=75)


# ==================== 10. 功能頁面 5：🚨 全國 SOS 緊急求救專區 (一鍵喚起原生 SMS 簡訊) ====================
elif st.session_state.current_page == "sos":
    st.markdown('<div class="back-btn">', unsafe_allow_html=True)
    if st.button("← 返回主頁面", key="back_sos"):
        st.session_state.current_page = "menu"
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("""
    <div class="card" style="border-left:5px solid #C62828; background-color:#FFEBEE;">
        <h3 style="margin-top:0px; color:#B71C1C;">🚨 全國緊急求救與精準 GPS 定位通報</h3>
        <p style="font-size:0.9rem; color:#C62828; margin-bottom:0;">如在戶外遇到緊急情況，請保持冷靜。點擊下方專線直撥或<b>點擊按鈕自動發送一鍵 SMS 求救簡訊</b>：</p>
    </div>
    """, unsafe_allow_html=True)

    # 🎯 使用 window.top.location.href 強制突破 iframe 限制喚起手機原生 SMS App
    sos_gps_js_template = """
    <div style="text-align:center; padding:10px; background-color:#FFEBEE; border-radius:10px; border:1px solid #FFCDD2; margin-bottom:12px;">
        <div id="sosGpsStatus" style="font-size:0.9rem; color:#C62828; font-weight:bold; margin-bottom:8px;">
            📡 正在感應當前衛星精確 SOS GPS 座標...
        </div>
    </div>

    <div style="background-color:#FFFFFF; border-radius:12px; padding:16px; border-left:5px solid #C62828; box-shadow:0 2px 10px rgba(0,0,0,0.04); margin-bottom:16px; text-align:center;">
        <h4 style="color:#C62828; margin-top:0; font-size:1.05rem;">📲 一鍵發送 SMS 求救簡訊 (自動帶入號碼與座標)</h4>
        
        <div style="margin-bottom:12px;">
            <a id="smsLink" href="javascript:void(0);" onclick="triggerSms(); return false;" target="_top" style="text-decoration:none;">
                <div style="background-color:#C62828; color:white; font-size:1.15rem; font-weight:bold; padding:14px; border-radius:10px; box-shadow:0 4px 10px rgba(198,40,40,0.3); cursor:pointer;">
                    💬 點擊自動開啟手機簡訊 App 發送求救簡訊
                </div>
            </a>
        </div>

        <p style="font-size:0.85rem; color:#666; text-align:left; margin-bottom:4px; font-weight:bold;">📋 簡訊預覽內容：</p>
        <div id="smsPreview" style="background-color:#F5F5F5; border-radius:8px; border:1px solid #E0E0E0; padding:10px; font-family:monospace; font-size:0.85rem; text-align:left; color:#333; word-break:break-all;">
            【🚨 SOS 全國緊急求救通報】<br>
            求救人暱稱：__USER_NICK__<br>
            當前精確 GPS 座標：感應中...<br>
            請救援隊儘快聯繫搜救！
        </div>
    </div>

    <script>
        var currentSmsText = "【🚨 SOS 全國緊急求救通報】\\n" +
                           "求救人暱稱：__USER_NICK__\\n" +
                           "當前精確 GPS 座標：感應中...\\n" +
                           "請救援隊儘快聯繫搜救！";

        function updateSmsButton(lat, lon) {
            var nick = "__USER_NICK__";
            currentSmsText = "【🚨 SOS 全國緊急求救通報】\\n" +
                               "求救人暱稱：" + nick + "\\n" +
                               "當前精確 GPS 座標：緯度 " + lat.toFixed(5) + ", 經度 " + lon.toFixed(5) + "\\n" +
                               "地圖位置導航：https://maps.google.com/?q=" + lat.toFixed(5) + "," + lon.toFixed(5) + "\\n" +
                               "請救援隊儘快聯繫搜救！";

            var htmlPreview = "【🚨 SOS 全國緊急求救通報】<br>" +
                              "求救人暱稱：" + nick + "<br>" +
                              "當前精確 GPS 座標：緯度 " + lat.toFixed(5) + ", 經度 " + lon.toFixed(5) + "<br>" +
                              "地圖位置導航：https://maps.google.com/?q=" + lat.toFixed(5) + "," + lon.toFixed(5) + "<br>" +
                              "請救援隊儘快聯繫搜救！";
            document.getElementById("smsPreview").innerHTML = htmlPreview;
        }

        function triggerSms() {
            var isIOS = /iPad|iPhone|iPod/.test(navigator.userAgent) && !window.MSStream;
            var separator = isIOS ? '&' : '?';
            var encodedText = encodeURIComponent(currentSmsText);
            var smsUrl = "sms:110" + separator + "body=" + encodedText;

            try {
                window.top.location.href = smsUrl;
            } catch(e) {
                window.location.href = smsUrl;
            }
        }

        if (navigator.geolocation) {
            navigator.geolocation.getCurrentPosition(function(position) {
                var lat = position.coords.latitude;
                var lon = position.coords.longitude;
                var accuracy = Math.round(position.coords.accuracy);
                
                document.getElementById("sosGpsStatus").innerHTML = "✅ 已鎖定極速 GPS 座標：緯度 " + lat.toFixed(5) + ", 經度 " + lon.toFixed(5) + " (誤差 ±" + accuracy + "米)";
                
                updateSmsButton(lat, lon);
            }, function(error) {
                document.getElementById("sosGpsStatus").innerHTML = "⚠️ 請允許定位權限以取得精確求救座標";
            }, {
                enableHighAccuracy: true,
                maximumAge: 0,
                timeout: 8000
            });
        }
    </script>
    """

    nick_name = st.session_state.user_nickname if st.session_state.user_nickname else "遊客"

    rendered_sos_html = sos_gps_js_template.replace("__USER_NICK__", str(nick_name))

    st.components.v1.html(rendered_sos_html, height=270)

    st.markdown("##### 📞 全國 / 港澳緊急救援直撥專線")

    col_sos1, col_sos2 = st.columns(2)
    with col_sos1:
        st.markdown("""
        <a href="tel:110" target="_top" style="text-decoration:none;">
            <div style="background-color:#C62828; color:white; text-align:center; padding:12px; border-radius:10px; font-weight:bold; margin-bottom:10px;">
                📞 110 公安報案熱線
            </div>
        </a>
        <a href="tel:120" target="_top" style="text-decoration:none;">
            <div style="background-color:#C62828; color:white; text-align:center; padding:12px; border-radius:10px; font-weight:bold; margin-bottom:10px;">
                📞 120 醫療急救中心
            </div>
        </a>
        """, unsafe_allow_html=True)

    with col_sos2:
        st.markdown("""
        <a href="tel:119" target="_top" style="text-decoration:none;">
            <div style="background-color:#C62828; color:white; text-align:center; padding:12px; border-radius:10px; font-weight:bold; margin-bottom:10px;">
                📞 119 消防救援熱線
            </div>
        </a>
        <a href="tel:999" target="_top" style="text-decoration:none;">
            <div style="background-color:#0277BD; color:white; text-align:center; padding:12px; border-radius:10px; font-weight:bold; margin-bottom:10px;">
                📞 999 港澳緊急求救
            </div>
        </a>
        """, unsafe_allow_html=True)

    st.info("💡 提示：點擊上方 SMS 簡訊發送按鈕，手機會自動開啟簡訊 App，按下發送即可迅速向搜救隊通報您的精確位置！")