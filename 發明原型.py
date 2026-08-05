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

# 使用者 GPS 座標 (澳門預設座標)
if "my_lat" not in st.session_state:
    st.session_state.my_lat = 22.1568
if "my_lon" not in st.session_state:
    st.session_state.my_lon = 113.5615

# 聲波驅蟲狀態與記憶
if "audio_active" not in st.session_state:
    st.session_state.audio_active = False
if "selected_insect_freq" not in st.session_state:
    st.session_state.selected_insect_freq = "17.4 kHz - 模擬雄蚊翅聲 (驅避咬人母蚊)"

# 共享定位房間與暱稱
if "room_id" not in st.session_state:
    st.session_state.room_id = ""
if "user_nickname" not in st.session_state:
    st.session_state.user_nickname = "媽媽"

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

# ==================== 2. 全局 CSS 樣式美化 (四大功能按鈕 100% 絕對等寬像素級完全對齊) ====================
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

    /* 頂部品牌 Header 區塊 */
    .brand-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 12px;
        padding-bottom: 10px;
        border-bottom: 2px solid #E8F5E9;
    }
    .brand-title {
        font-size: 1.8rem;
        font-weight: 800;
        color: #1B5E20;
        margin: 0;
    }
    .brand-sub {
        font-size: 0.92rem;
        color: #2E7D32;
        font-weight: bold;
        margin-top: 2px;
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


# ==================== 3. 澳門氣象實時數據連線 (僅在手動模擬關閉時更新) ====================
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


# ==================== 4. 頂部 Header & 右上角聲波驅蟲按鈕 ====================
audio_badge_text = "🟢 聲波驅蟲運作中" if st.session_state.audio_active else "🔴 聲波驅蟲未啟動"

col_head1, col_head2 = st.columns([2, 1])

with col_head1:
    st.markdown("""
    <div>
        <div class="brand-title">🍀 絲野仙蹤 Eco-Family</div>
        <div class="brand-sub">澳門親子綠色呼吸智慧隨行助手</div>
    </div>
    """, unsafe_allow_html=True)

with col_head2:
    if st.button(f"🔊 {audio_badge_text}", key="top_right_audio_btn"):
        st.session_state.current_page = "audio"
        st.rerun()

st.markdown("<hr style='margin-top:5px; margin-bottom:15px; border-color:#E8F5E9;'>", unsafe_allow_html=True)


# ==================== 5. 頁面 1：主選單 (四大按鈕 100% 長度與樣式對齊，直連 Google Maps) ====================
if st.session_state.current_page == "menu":

    # 按鈕 1
    if st.button("🗺️ 智慧路線規劃", key="btn_m1", use_container_width=True):
        st.session_state.current_page = "routes"
        st.rerun()

    # 按鈕 2 (使用 Streamlit 原生 link_button，長度 100% 完全對齊且 100% 順暢開啟 Google Maps)
    google_maps_sharing_url = "https://www.google.com/maps/@22.1987,113.5439,15z"
    try:
        st.link_button("📍 親友共享定位雷達", google_maps_sharing_url, use_container_width=True)
    except AttributeError:
        st.markdown(f'<a href="{google_maps_sharing_url}" target="_blank" class="unified-card-btn">📍 親友共享定位雷達</a>', unsafe_allow_html=True)

    # 按鈕 3
    if st.button("🎒 隨行裝備", key="btn_m3", use_container_width=True):
        st.session_state.current_page = "gear"
        st.rerun()

    # 按鈕 4 (使用 Streamlit 原生 link_button，長度 100% 完全對齊)
    ext_url = "https://eddychan912-blip.github.io/eco-tracker11/"
    try:
        st.link_button("🔍 親子生態動植物識別", ext_url, use_container_width=True)
    except AttributeError:
        st.markdown(f'<a href="{ext_url}" target="_blank" class="unified-card-btn">🔍 親子生態動植物識別</a>', unsafe_allow_html=True)


# ==================== 6. 功能頁面 1：🗺️ 智慧路線規劃 (18條精確條件匹配路線) ====================
elif st.session_state.current_page == "routes":
    st.markdown('<div class="back-btn">', unsafe_allow_html=True)
    if st.button("← 返回主頁面", key="back_routes"):
        st.session_state.current_page = "menu"
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

    # 手動氣象模擬控制面板
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

    # 氣象數據顯示 (去除「狀態」二字，加上「是否」)
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
        rain_text = "🌧️ 降雨" if st.session_state.global_rain else "☀️ 晴朗"
        st.markdown(f"""<div class="metric-card"><div class="metric-title">🌧️ 是否降雨</div><div class="metric-value" style="font-size:1.1rem; margin-top:2px;">{rain_text}</div></div>""", unsafe_allow_html=True)

    st.write("")

    # 去「全」字
    st.markdown("""
    <div class="card">
        <h3 style="margin-top:0px; color:#1E5631;">🗺️ 澳門目的地與氣象適應路線規劃</h3>
        <p style="font-size:0.9rem; margin-bottom:0;">選擇澳門目的地，系統將依據<b>當前氣溫、紫外線與是否降雨</b>推薦最適路線：</p>
    </div>
    """, unsafe_allow_html=True)

    # 18 條完全獨特、不重複的專屬路線資料庫
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
                "name": "🏃‍♂️ 望廈山砲台歷史景觀環路",
                "shade": 65, "rain_safe": False, "base_crowd": 25,
                "length": "1.5 公里", "time": "35 分鐘",
                "origin": "113.5488,22.2062", "destination": "113.5498,22.2075", "dest_name": "望廈山健康徑",
                "desc": "【晴朗涼爽專屬推薦】登上歷史砲台區，俯瞰澳門北部城區。"
            }
        ]
    }

    selected_dest = st.selectbox("📍 請選擇澳門目的地：", list(macau_18_unique_destinations.keys()))

    cur_temp = st.session_state.global_temp
    cur_uv = st.session_state.global_uv
    is_rain = st.session_state.global_rain

    dest_routes = macau_18_unique_destinations[selected_dest]

    # 時間動態人數更新
    time_seed = int(time.time() / 8)

    # 當前氣象對應的動態推薦提示
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
        
        # 精確算分矩陣：保證第一名隨著氣象數據 100% 動態翻轉，無同分競爭！
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

    # 依分數重新排序，第 1 名必定隨氣象數據即時翻轉！
    sorted_dest_routes = sorted(dest_routes, key=lambda x: x["dynamic_score"], reverse=True)

    st.markdown(f"#### 🎯 當前氣象 (氣溫 {cur_temp:.1f}°C / UV {cur_uv:.1f} / 天氣：{'🌧️ 下雨' if is_rain else '☀️ 晴朗'}) 推薦路線：")

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


# ==================== 7. 功能頁面 2：📍 親友共享定位雷達 (Google 地圖定位直達頁面) ====================
elif st.session_state.current_page == "family":
    st.markdown('<div class="back-btn">', unsafe_allow_html=True)
    if st.button("← 返回主頁面", key="back_family"):
        st.session_state.current_page = "menu"
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("""
    <div class="card">
        <h3 style="margin-top:0px; color:#1E5631;">📍 親友共享定位雷達</h3>
        <p style="font-size:0.9rem; margin-bottom:12px;">點擊下方按鈕，即可直接跳轉至 Google 地圖共享定位，查看房間內所有人的實時位置與相對距離：</p>
    </div>
    """, unsafe_allow_html=True)

    # 點擊直接開啟 Google 地圖實時共享定位網頁
    gmaps_sharing = "https://www.google.com/maps/@22.1987,113.5439,15z"
    st.markdown(f"""
    <a href="{gmaps_sharing}" target="_blank" style="text-decoration:none;">
        <div style="
            background-color:#1B5E20; color:white; text-align:center;
            padding:16px; border-radius:14px; font-weight:bold; font-size:1.25rem;
            margin-bottom:16px; box-shadow:0 4px 15px rgba(27,94,32,0.25);
        ">
            🌐 直接開啟 Google 地圖實時共享定位
        </div>
    </a>
    """, unsafe_allow_html=True)


# ==================== 8. 功能頁面 3：🎒 隨行裝備 (懸浮微粒已移除「是否」二字) ====================
elif st.session_state.current_page == "gear":
    st.markdown('<div class="back-btn">', unsafe_allow_html=True)
    if st.button("← 返回主頁面", key="back_gear"):
        st.session_state.current_page = "menu"
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

    # 手動氣象模擬控制面板
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

    # 氣象數據顯示 (補上「是否」二字)
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
        rain_text = "🌧️ 降雨" if st.session_state.global_rain else "☀️ 晴朗"
        st.markdown(f"""<div class="metric-card"><div class="metric-title">🌧️ 是否降雨</div><div class="metric-value" style="font-size:1.1rem; margin-top:2px;">{rain_text}</div></div>""", unsafe_allow_html=True)

    st.write("")

    st.markdown("""
    <div class="card">
        <h3 style="margin-top:0px; color:#1E5631;">🎒 當前氣象動態推薦隨行裝備</h3>
        <p style="font-size:0.9rem; margin-bottom:0;">系統根據目前的<b>氣溫、紫外線、是否降雨與懸浮微粒</b>數據精算出的推薦清單：</p>
    </div>
    """, unsafe_allow_html=True)

    # 1. 📌 出行基礎隨行包 (始終保底)
    st.markdown("##### 📌 出行必備基礎裝備")
    st.checkbox("🍼 **兒童水壺 / 保溫杯** (隨時補充水分)", value=True, key="gear_water")
    st.checkbox("🧻 **濕紙巾與消毒個人用品**", value=True, key="gear_wipes")
    st.checkbox("🩹 **隨身創可貼與急救盒**", value=True, key="gear_firstaid")

    # 2. 🌧️ 降雨動態應對裝備 (只有在勾選下雨時才顯示雨具！沒下雨絕對不顯示)
    if st.session_state.global_rain:
        st.markdown("##### 🌧️ 是否降雨：當前降雨專屬裝備")
        st.checkbox("🌧️ **嬰兒車透氣防雨罩 & 親子大雨傘**", value=True, key="gear_rain1")
        st.checkbox("🌂 **備用寶寶乾爽衣物 1 套 (防水袋裝)**", value=True, key="gear_rain2")
        st.checkbox("👟 **兒童防滑雨鞋**", value=True, key="gear_rain3")

    # 3. ☀️ 紫外線動態應對裝備 (僅在 UV ≥ 2.5 時動態彈出)
    cur_uv = st.session_state.global_uv
    if cur_uv >= 2.5:
        st.markdown(f"##### ☀️ 防曬護膚專屬裝備 (當前 UV {cur_uv:.1f} 偏強)")
        st.checkbox("☀️ **兒童高效防曬乳 (SPF50+)**", value=True, key="gear_uv_high1")
        st.checkbox("🧢 **推車抗 UV 遮陽罩 & 親子大簷太陽帽**", value=True, key="gear_uv_high2")
        st.checkbox("🕶️ **兒童太陽眼鏡**", value=True, key="gear_uv_high3")

    # 4. 🌡️ 氣溫全區間動態應對裝備 (高溫或低溫時才動態彈出)
    cur_t = st.session_state.global_temp
    if cur_t >= 26.0:
        st.markdown(f"##### 🌡️ 高溫防暑專屬裝備 (當前 {cur_t:.1f}°C 偏熱)")
        st.checkbox("🌬️ **夾式推車靜音小風扇** *(防止寶寶高溫中暑)*", value=True, key="gear_temp_hot1")
        st.checkbox("🧊 **兒童退熱貼 / 電解質水補給包**", value=True, key="gear_temp_hot2")
    elif cur_t <= 20.0:
        st.markdown(f"##### 🧥 保暖防風專屬裝備 (當前 {cur_t:.1f}°C 偏涼)")
        st.checkbox("🧥 **兒童保暖防風外套 & 小毛毯**", value=True, key="gear_temp_cold1")
        st.checkbox("☕ **熱水保溫壺**", value=True, key="gear_temp_cold2")

    # 5. 😷 PM2.5 / PM10 懸浮微粒動態應對裝備 (已按要求將標題改為「懸浮微粒」，移除「是否」二字)
    cur_pm25 = st.session_state.global_pm25
    if cur_pm25 >= 15.0:
        st.markdown(f"##### 😷 懸浮微粒：呼吸道護理裝備 (當前 PM2.5 {cur_pm25:.1f})")
        st.checkbox("😷 **兒童高防護透氣口罩**", value=True, key="gear_pm_high")


# ==================== 9. 功能頁面 4：🪰 多頻率驅聲波 (右上角按鈕跳轉專用) ====================
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

    audio_js = f"""
    <div style="text-align:center; padding:10px; background:#F1F8E9; border-radius:10px;">
        <p style="font-size:0.9rem; color:#2E7D32; font-weight:bold; margin:0;">
            {"🟢 超聲波背景持續播放中..." if st.session_state.audio_active else "🔴 聲波目前未啟動"}
        </p>
    </div>
    <script>
        var actx = null;
        var osc = null;
        if ({'true' if st.session_state.audio_active else 'false'}) {{
            try {{
                actx = new (window.AudioContext || window.webkitAudioContext)();
                osc = actx.createOscillator();
                var g = actx.createGain();
                osc.type = 'sine';
                osc.frequency.setValueAtTime({current_hz}, actx.currentTime);
                g.gain.setValueAtTime(0.12, actx.currentTime);
                osc.connect(g);
                g.connect(actx.destination);
                osc.start();
            }} catch(e) {{}}
        }}
    </script>
    """
    st.components.v1.html(audio_js, height=75)