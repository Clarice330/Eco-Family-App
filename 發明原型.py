# -*- coding: utf-8 -*-
"""
🍀 絲野仙蹤 (Eco-Family) - 親子綠色呼吸智慧隨行助手
標準配置：3 大功能 (智慧路線規劃、隨行裝備、親子生態動植物識別外連)
+ 2 右上角小功能正方形按鈕 (🔊 驅蟲, 🚨 一鍵求救)
+ 頂部「👵 關愛大字體模式」開關
+ 前兩項核心功能皆含「🌤️ 手動氣象模擬測試面板」
"""

import streamlit as st
import requests
import urllib.parse
import streamlit.components.v1 as components

query_params = st.query_params

if "page" in query_params and query_params["page"]:
    st.session_state.current_page = query_params["page"]

# 氣象實時與模擬數據
if "global_temp" not in st.session_state:
    st.session_state.global_temp = 22.5
if "global_uv" not in st.session_state:
    st.session_state.global_uv = 1.2
if "global_rain" not in st.session_state:
    st.session_state.global_rain = False
if "global_wind" not in st.session_state:
    st.session_state.global_wind = 10.0
if "global_pm25" not in st.session_state:
    st.session_state.global_pm25 = 12.0
if "global_pm10" not in st.session_state:
    st.session_state.global_pm10 = 24.0
if "global_aqi" not in st.session_state:
    st.session_state.global_aqi = 28.0

# 是否開啟手動氣象覆蓋測試
if "override_weather" not in st.session_state:
    st.session_state.override_weather = False

# 關愛大字體模式開關
if "is_elder_mode" not in st.session_state:
    st.session_state.is_elder_mode = False

# 使用者 GPS 座標 (預設澳門座標)
if "my_lat" not in st.session_state:
    st.session_state.my_lat = 22.1568
if "my_lon" not in st.session_state:
    st.session_state.my_lon = 113.5615

# 小功能 1：驅聲波狀態與記憶
if "audio_active" not in st.session_state:
    st.session_state.audio_active = False
if "selected_insect_freq" not in st.session_state:
    st.session_state.selected_insect_freq = "17.4 kHz - 模擬雄蚊翅聲 (驅避咬人母蚊)"

# 預設暱稱
if "user_nickname" not in st.session_state:
    st.session_state.user_nickname = "親兒子/女"

# 導航頁面狀態
if "current_page" not in st.session_state:
    st.session_state.current_page = "menu"

st.set_page_config(
    page_title="絲野仙蹤 Eco-Family",
    page_icon="🍀",
    layout="centered",
    initial_sidebar_state="collapsed"
)

is_elder = st.session_state.is_elder_mode

# 動態計算各種層級的字體大小 (外框尺寸固定 85px，文字滿框放大)
btn_font_size = "1.85rem" if is_elder else "1.2rem"
btn_padding = "0px 4px" if is_elder else "12px 16px"
btn_line_height = "1.1" if is_elder else "1.3"

card_body_size = "1.3rem" if is_elder else "0.9rem"
card_h3_size = "1.6rem" if is_elder else "1.2rem"
card_h4_size = "1.45rem" if is_elder else "1.05rem"
metric_val_size = "1.8rem" if is_elder else "1.35rem"
metric_title_size = "1.1rem" if is_elder else "0.85rem"
label_font_size = "1.3rem" if is_elder else "0.95rem"

st.markdown(f"""
<style>
    .stApp {{
        background-color: #F4F7F4;
        color: #1B4332;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
    }}
    
    section[data-testid="stSidebar"] {{
        display: none;
    }}

    /* 強制頂部欄在所有手機螢幕下都橫向緊湊排列，絕不換行或推至螢幕外 */
    div[data-testid="stHorizontalBlock"]:first-of-type {{
        display: flex !important;
        flex-direction: row !important;
        flex-wrap: nowrap !important;
        align-items: center !important;
        justify-content: space-between !important;
        gap: 4px !important;
        width: 100% !important;
    }}

    div[data-testid="stHorizontalBlock"]:first-of-type > div[data-testid="column"]:nth-child(1) {{
        flex: 1 1 auto !important;
        min-width: 0 !important;
    }}

    div[data-testid="stHorizontalBlock"]:first-of-type > div[data-testid="column"]:nth-child(2),
    div[data-testid="stHorizontalBlock"]:first-of-type > div[data-testid="column"]:nth-child(3) {{
        flex: 0 0 auto !important;
        width: 42px !important;
        min-width: 42px !important;
    }}

    /* 按鈕容器全寬調整 */
    div[data-testid="stButton"] {{
        width: 100% !important;
        margin: 0 !important;
        padding: 0 !important;
        box-sizing: border-box !important;
    }}

    /* 綠色系標準選單大按鈕 (外框高度固定 85px) */
    div[data-testid="stButton"] > button {{
        width: 100% !important;
        background: linear-gradient(135deg, #FFFFFF 0%, #F1F8E9 100%) !important;
        border-radius: 18px !important;
        height: 85px !important;
        min-height: 85px !important;
        max-height: 85px !important;
        box-shadow: 0 4px 12px rgba(46, 125, 50, 0.08) !important;
        border: 2px solid #A5D6A7 !important;
        text-align: center !important;
        margin: 0 0 14px 0 !important;
        padding: {btn_padding} !important;
        transition: all 0.2s ease-in-out !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        box-sizing: border-box !important;
        white-space: normal !important;
        word-break: break-word !important;
    }}

    /* 強制鎖定大按鈕內部所有層級 (p, span, div) 的字體大小與行高 */
    div[data-testid="stButton"] > button,
    div[data-testid="stButton"] > button *,
    div[data-testid="stButton"] > button p,
    div[data-testid="stButton"] > button span,
    div[data-testid="stButton"] > button div {{
        font-size: {btn_font_size} !important;
        font-weight: 800 !important;
        line-height: {btn_line_height} !important;
        color: #1B5E20 !important;
        margin: 0 !important;
        padding: 0 !important;
    }}

    div[data-testid="stButton"] > button:hover {{
        border-color: #2E7D32 !important;
        background: linear-gradient(135deg, #E8F5E9 0%, #C8E6C9 100%) !important;
        box-shadow: 0 6px 16px rgba(46, 125, 50, 0.15) !important;
        transform: translateY(-2px) !important;
    }}

    /* 右上角小功能專屬正方形小按鈕 (42px x 42px) */
    .top-square-btn div[data-testid="stButton"] {{
        margin: 0 !important;
        width: 42px !important;
    }}

    .top-square-btn div[data-testid="stButton"] > button {{
        width: 42px !important;
        min-width: 42px !important;
        max-width: 42px !important;
        height: 42px !important;
        min-height: 42px !important;
        max-height: 42px !important;
        border-radius: 12px !important;
        margin: 0 !important;
        padding: 0 !important;
        box-shadow: 0 2px 6px rgba(0,0,0,0.06) !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
    }}
    
    .top-square-audio div[data-testid="stButton"] > button {{
        background: #E8F5E9 !important;
        border: 1.5px solid #81C784 !important;
    }}
    .top-square-audio div[data-testid="stButton"] > button,
    .top-square-audio div[data-testid="stButton"] > button *,
    .top-square-audio div[data-testid="stButton"] > button p,
    .top-square-audio div[data-testid="stButton"] > button span {{
        color: #1B5E20 !important;
        font-size: 1.15rem !important;
        line-height: 1 !important;
    }}

    .top-square-sos div[data-testid="stButton"] > button {{
        background: #FFEBEE !important;
        border: 1.5px solid #E53935 !important;
    }}
    .top-square-sos div[data-testid="stButton"] > button,
    .top-square-sos div[data-testid="stButton"] > button *,
    .top-square-sos div[data-testid="stButton"] > button p,
    .top-square-sos div[data-testid="stButton"] > button span {{
        color: #C62828 !important;
        font-size: 1.15rem !important;
        line-height: 1 !important;
    }}

    /* 內文卡片與內部文字放大樣式 */
    .card {{
        background-color: #FFFFFF;
        border-radius: 16px;
        padding: 18px;
        box-shadow: 0 2px 10px rgba(46, 125, 50, 0.06);
        border-left: 5px solid #2E7D32;
        border-top: 1px solid #E8F5E9;
        border-right: 1px solid #E8F5E9;
        border-bottom: 1px solid #E8F5E9;
        margin-bottom: 16px;
        font-size: {card_body_size} !important;
    }}

    .card p, .card span, .card li, .card div {{
        font-size: {card_body_size} !important;
        line-height: 1.5 !important;
    }}

    .card h3 {{
        font-size: {card_h3_size} !important;
    }}

    .card h4 {{
        font-size: {card_h4_size} !important;
    }}

    /* 數據卡片放大 */
    .metric-card {{
        background-color: #E8F5E9;
        border-radius: 12px;
        padding: 10px;
        text-align: center;
        border: 1px solid #C8E6C9;
        margin-bottom: 10px;
    }}
    .metric-title {{
        font-size: {metric_title_size} !important;
        color: #2E7D32;
        font-weight: bold;
    }}
    .metric-value {{
        font-size: {metric_val_size} !important;
        font-weight: bold;
        color: #1B5E20;
    }}

    /* Streamlit 輸入元件文字（多選框、單選按鈕、標籤等）放大 */
    label[data-testid="stWidgetLabel"] p,
    div[data-baseweb="checkbox"] span,
    div[data-baseweb="radio"] span,
    div[data-baseweb="select"] span {{
        font-size: {label_font_size} !important;
        font-weight: 600 !important;
    }}

    .badge-green {{
        background-color: #2E7D32;
        color: white;
        padding: 4px 10px;
        border-radius: 10px;
        font-size: {"1.0rem" if is_elder else "0.8rem"};
        font-weight: bold;
    }}
    .badge-star {{
        background-color: #E65100;
        color: white;
        padding: 4px 10px;
        border-radius: 10px;
        font-size: {"1.0rem" if is_elder else "0.8rem"};
        font-weight: bold;
    }}

    .back-btn button {{
        background-color: #E8F5E9 !important;
        color: #1B5E20 !important;
        font-weight: bold !important;
        padding: 8px 16px !important;
        border-radius: 10px !important;
        border: 1px solid #A5D6A7 !important;
        margin-bottom: 16px !important;
        height: auto !important;
        min-height: auto !important;
    }}
    .back-btn button * {{
        font-size: {"1.2rem" if is_elder else "0.95rem"} !important;
    }}

    /* 動植物辨識連結卡片樣式 */
    .link-card-button {{
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        width: 100% !important;
        height: 85px !important;
        background: linear-gradient(135deg, #FFFFFF 0%, #F1F8E9 100%) !important;
        border-radius: 18px !important;
        border: 2px solid #A5D6A7 !important;
        box-shadow: 0 4px 12px rgba(46, 125, 50, 0.08) !important;
        text-decoration: none !important;
        margin-bottom: 14px !important;
        box-sizing: border-box !important;
        transition: all 0.2s ease-in-out !important;
    }}
    .link-card-button:hover {{
        border-color: #2E7D32 !important;
        background: linear-gradient(135deg, #E8F5E9 0%, #C8E6C9 100%) !important;
        box-shadow: 0 6px 16px rgba(46, 125, 50, 0.15) !important;
        transform: translateY(-2px) !important;
    }}
    .link-card-text {{
        font-size: {btn_font_size} !important;
        font-weight: 800 !important;
        line-height: {btn_line_height} !important;
        color: #1B5E20 !important;
        text-align: center !important;
    }}
</style>
""", unsafe_allow_html=True)

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

# 頂部列：左側標題，右側兩個小正方形按鈕
col_title, col_audio_sq, col_sos_sq = st.columns([2.5, 0.5, 0.5])

with col_title:
    title_font_size = "1.15rem" if is_elder else "1.05rem"
    sub_title_size = "0.75rem" if is_elder else "0.68rem"
    st.markdown(f"""
    <div style="text-align: left; padding: 0px; overflow: hidden;">
        <div style="font-size: {title_font_size}; font-weight: 800; color: #1B5E20; letter-spacing: -0.3px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">
            🍀 絲野仙蹤 Eco-Family
        </div>
        <div style="font-size: {sub_title_size}; color: #2E7D32; margin-top: 1px; font-weight: 600; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">
            澳門親子綠色呼吸智慧隨行助手
        </div>
    </div>
    """, unsafe_allow_html=True)

# 小功能 1：正方形 🔊 驅蟲按鈕
with col_audio_sq:
    st.markdown('<div class="top-square-btn top-square-audio">', unsafe_allow_html=True)
    audio_btn_label = "🔊🟢" if st.session_state.audio_active else "🔊🔴"
    if st.button(audio_btn_label, key="btn_top_audio", help="驅蟲聲波設置"):
        st.session_state.current_page = "audio"
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

# 小功能 2：正方形 🚨 求救按鈕
with col_sos_sq:
    st.markdown('<div class="top-square-btn top-square-sos">', unsafe_allow_html=True)
    if st.button("🚨", key="btn_top_sos", help="一鍵求救與定位"):
        st.session_state.current_page = "sos"
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

# 關愛大字體模式開關
elder_toggle = st.toggle("👵 關愛大字體模式", value=st.session_state.is_elder_mode, key="elder_mode_toggle")
if elder_toggle != st.session_state.is_elder_mode:
    st.session_state.is_elder_mode = elder_toggle
    st.rerun()

st.markdown("<hr style='margin-top: 8px; margin-bottom: 20px; border: none; border-top: 1px solid #C8E6C9;'>", unsafe_allow_html=True)

if st.session_state.current_page == "menu":

    # 1. 大功能一：智慧路線規劃
    if st.button("🗺️ 智慧路線規劃", key="btn_m1", use_container_width=True):
        st.session_state.current_page = "routes"
        st.rerun()

    # 2. 大功能二：隨行裝備
    if st.button("🎒 隨行裝備", key="btn_m2", use_container_width=True):
        st.session_state.current_page = "gear"
        st.rerun()

    # 3. 大功能三：親子生態動植物識別 (連結跳轉至指定線上辨識平台)
    st.markdown(f"""
    <a href="https://eddychan912-blip.github.io/eco-tracker11/" target="_blank" class="link-card-button">
        <div class="link-card-text">🔍 親子生態動植物識別</div>
    </a>
    """, unsafe_allow_html=True)

elif st.session_state.current_page == "routes":
    st.markdown('<div class="back-btn">', unsafe_allow_html=True)
    if st.button("← 返回主頁面", key="back_routes"):
        st.session_state.current_page = "menu"
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

    # 氣象手動覆蓋與模擬調試控制面板 (大功能 1 手動模擬)
    with st.expander("🌤️ 手動氣象模擬 / 測試調試面板", expanded=st.session_state.override_weather):
        st.session_state.override_weather = st.checkbox("開啟手動氣象模擬 (覆蓋 API 數據)", value=st.session_state.override_weather, key="override_routes")
        if st.session_state.override_weather:
            st.info("💡 已啟用氣象模擬模式，您可以隨意調節以下環境數值測試路線動態推薦：")
            c1, c2, c3 = st.columns(3)
            with c1:
                st.session_state.global_temp = st.slider("🌡️ 氣溫 (°C)", -5.0, 40.0, float(st.session_state.global_temp), key="temp_r")
                st.session_state.global_uv = st.slider("☀️ 紫外線 (UV)", 0.0, 12.0, float(st.session_state.global_uv), key="uv_r")
            with c2:
                st.session_state.global_rain = st.checkbox("🌧️ 是否降雨", value=st.session_state.global_rain, key="rain_r")
                st.session_state.global_wind = st.slider("🌬️ 風速 (km/h)", 0.0, 60.0, float(st.session_state.global_wind), key="wind_r")
            with c3:
                st.session_state.global_pm25 = st.slider("🍃 PM2.5 (μg/m³)", 0.0, 200.0, float(st.session_state.global_pm25), key="pm25_r")

    st.markdown("##### ☁️ 當前評估環境數據")
    r1, r2, r3, r4 = st.columns(4)
    with r1:
        st.markdown(f"""<div class="metric-card"><div class="metric-title">🌡️ 氣溫</div><div class="metric-value">{st.session_state.global_temp:.1f}°C</div></div>""", unsafe_allow_html=True)
    with r2:
        st.markdown(f"""<div class="metric-card"><div class="metric-title">☀️ 紫外線</div><div class="metric-value">UV {st.session_state.global_uv:.1f}</div></div>""", unsafe_allow_html=True)
    with r3:
        st.markdown(f"""<div class="metric-card"><div class="metric-title">🍃 PM2.5</div><div class="metric-value">{st.session_state.global_pm25:.1f}</div></div>""", unsafe_allow_html=True)
    with r4:
        rain_text = "降雨中" if st.session_state.global_rain else "無雨"
        st.markdown(f"""<div class="metric-card"><div class="metric-title">🌧️ 降雨</div><div class="metric-value">{rain_text}</div></div>""", unsafe_allow_html=True)

    # 依模擬或實時氣象自動判斷路線推薦狀態
    weather_recommend = "rain" if st.session_state.global_rain else ("hot" if (st.session_state.global_temp >= 28.0 or st.session_state.global_uv >= 5.0) else "normal")

    st.markdown("""
    <div class="card">
        <h3 style="margin-top:0px; color:#1B5E20;">🗺️ 目的地與設施路線規劃</h3>
        <p style="margin-bottom:0; color:#2E7D32;">根據氣象狀態（降雨/高溫）、坡度需求與母嬰室設施自動調整最佳路線推薦：</p>
    </div>
    """, unsafe_allow_html=True)

    unique_destinations = {
        "大潭山步行徑 (氹仔區)": [
            {
                "id": 101, "target_condition": "rain",
                "name": "🌲 大潭山斜行升降機風雨遮陽主線",
                "shade": 95, "slope": "平緩 (斜行電梯/無障礙)", "has_nursery": True,
                "length": "2.2 公里", "time": "40 分鐘",
                "origin": "113.5615,22.1568", "destination": "113.5630,22.1580", "dest_name": "大潭山斜行升降機",
                "desc": "設有無障礙風雨連廊與斜行電梯，設有母嬰洗手間，95% 高樹蔭覆蓋。"
            },
            {
                "id": 102, "target_condition": "hot",
                "name": "🦋 大潭山谷地賞蝶樹蔭林陰密徑",
                "shade": 90, "slope": "中等緩坡", "has_nursery": True,
                "length": "1.8 公里", "time": "35 分鐘",
                "origin": "113.5615,22.1568", "destination": "113.5620,22.1595", "dest_name": "大潭山郊野公園",
                "desc": "茂密山谷樹蔭天然擋陽，郊野公園內備有母嬰室及休息亭。"
            }
        ],
        "松山 (東望洋) 健康徑": [
            {
                "id": 201, "target_condition": "rain",
                "name": "🗼 東望洋燈塔與防空洞展館歷史線",
                "shade": 60, "slope": "平緩道路", "has_nursery": True,
                "length": "2.5 公里", "time": "50 分鐘",
                "origin": "113.5482,22.1965", "destination": "113.5498,22.1968", "dest_name": "東望洋燈塔",
                "desc": "途經松山防空洞展館，可隨時入內避雨，展館內設有母嬰設施。"
            },
            {
                "id": 202, "target_condition": "hot",
                "name": "🌿 松山公園高樹蔭綠亭遮陽漫步線",
                "shade": 92, "slope": "平緩道路", "has_nursery": True,
                "length": "1.2 公里", "time": "25 分鐘",
                "origin": "113.5482,22.1965", "destination": "113.5488,22.1972", "dest_name": "松山公園",
                "desc": "全線密集高大榕樹掩映，公園洗手間配備母嬰護理台。"
            }
        ]
    }

    col_sel1, col_sel2 = st.columns([2, 1])
    with col_sel1:
        selected_dest = st.selectbox("📍 請選擇目的地：", list(unique_destinations.keys()), key="dest_sel")
    with col_sel2:
        selected_slope = st.selectbox("🏔️ 坡度篩選：", ["全部坡度", "平緩 (斜行電梯/無障礙)", "平緩道路", "中等緩坡"], key="slope_sel")

    need_nursery = st.checkbox("🍼 僅顯示設有母嬰室設施之路線", value=False, key="nursery_ck")

    dest_routes = unique_destinations[selected_dest]
    for idx, route in enumerate(dest_routes):
        if need_nursery and not route["has_nursery"]:
            continue
        if selected_slope != "全部坡度" and route["slope"] != selected_slope:
            continue

        is_best = (route["target_condition"] == weather_recommend) or (weather_recommend == "normal" and idx == 0)
        badge = '<span class="badge-star">🌟 當前氣象首選推薦</span>' if is_best else '<span class="badge-green">推薦</span>'
        nav_url = f"https://uri.amap.com/navigation?from={route['origin']},Start&to={route['destination']},{urllib.parse.quote(route['dest_name'])}&mode=walk&policy=1&src=mypage&callnative=1"

        st.markdown(f"""
        <div class="card" style="{'border-left:6px solid #E65100; background-color:#FFFDE7;' if is_best else ''}">
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:6px;">
                <h4 style="margin:0; color:#1B5E20;">{route['name']}</h4>
                {badge}
            </div>
            <p style="color:#444; margin-bottom:8px;">{route['desc']}</p>
            <div style="color:#2E7D32; line-height:1.6; margin-bottom:12px;">
                <b>📏 長度：</b> {route['length']} | <b>⏱️ 時間：</b> {route['time']} | <b>⛰️ 坡度：</b> <b style="color:#0277BD;">{route['slope']}</b> | <b>🌳 樹蔭：</b> {route['shade']}%
            </div>
            <a href="{nav_url}" target="_blank" style="text-decoration:none;">
                <div style="background-color:#1B5E20; color:white; text-align:center; padding:10px; border-radius:10px; font-weight:bold;">
                    🧭 開啟地圖導航
                </div>
            </a>
        </div>
        """, unsafe_allow_html=True)

elif st.session_state.current_page == "gear":
    st.markdown('<div class="back-btn">', unsafe_allow_html=True)
    if st.button("← 返回主頁面", key="back_gear"):
        st.session_state.current_page = "menu"
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

    # 氣象手動覆蓋與模擬調試控制面板 (大功能 2 手動模擬)
    with st.expander("🌤️ 手動氣象模擬 / 測試調試面板", expanded=st.session_state.override_weather):
        st.session_state.override_weather = st.checkbox("開啟手動氣象模擬 (覆蓋 API 數據)", value=st.session_state.override_weather, key="override_gear")
        if st.session_state.override_weather:
            st.info("💡 已啟用氣象模擬模式，您可以隨意調節以下環境數值測試裝備動態推薦：")
            c1, c2, c3 = st.columns(3)
            with c1:
                st.session_state.global_temp = st.slider("🌡️ 氣溫 (°C)", -5.0, 40.0, float(st.session_state.global_temp), key="temp_g")
                st.session_state.global_uv = st.slider("☀️ 紫外線 (UV)", 0.0, 12.0, float(st.session_state.global_uv), key="uv_g")
            with c2:
                st.session_state.global_rain = st.checkbox("🌧️ 是否降雨", value=st.session_state.global_rain, key="rain_g")
                st.session_state.global_wind = st.slider("🌬️ 風速 (km/h)", 0.0, 60.0, float(st.session_state.global_wind), key="wind_g")
            with c3:
                st.session_state.global_pm25 = st.slider("🍃 PM2.5 (μg/m³)", 0.0, 200.0, float(st.session_state.global_pm25), key="pm25_g")

    st.markdown("""
    <div class="card">
        <h3 style="margin-top:0px; color:#1B5E20;">🎒 氣象動態隨行裝備建議</h3>
        <p style="margin-bottom:0; color:#2E7D32;">根據當前評估的實時/模擬氣象狀態，動態生成最適宜的裝備建議清單：</p>
    </div>
    """, unsafe_allow_html=True)

    # 1. 基礎必備裝備 (預設不勾選)
    st.markdown("##### 📌 出行基礎必備裝備")
    st.checkbox("🍼 **兒童專用水壺 / 保溫水杯**", value=False, key="gear_base_1")
    st.checkbox("🧻 **濕紙巾與消毒用品**", value=False, key="gear_base_2")
    st.checkbox("🩹 **隨身 OK 繃與急救護理包**", value=False, key="gear_base_3")

    # 2. 依據降雨動態推薦 (預設不勾選)
    if st.session_state.global_rain:
        st.markdown("##### 🌧️ 降雨天氣專屬裝備")
        st.checkbox("🌧️ **推車全覆蓋透氣防雨罩**", value=False, key="gear_rain_1")
        st.checkbox("☂️ **親子防風折疊雨傘**", value=False, key="gear_rain_2")
        st.checkbox("👕 **備用乾爽替換衣物 1 套**", value=False, key="gear_rain_3")

    # 3. 依據紫外線 (UV) 動態推薦 (預設不勾選)
    if st.session_state.global_uv >= 2.0:
        st.markdown("##### ☀️ 高紫外線防曬裝備 (UV ≥ 2.0)")
        st.checkbox("☀️ **兒童物理防曬乳 (SPF50+ / PA+++)**", value=False, key="gear_uv_1")
        st.checkbox("🧢 **大簷防曬遮陽帽**", value=False, key="gear_uv_2")
        if st.session_state.global_uv >= 5.0:
            st.checkbox("🕶️ **兒童抗 UV400 太陽眼鏡**", value=False, key="gear_uv_3")

    # 4. 依據溫度動態推薦 (預設不勾選)
    if st.session_state.global_temp >= 25.0:
        st.markdown("##### 🌡️ 高溫防暑降溫裝備 (≥ 25°C)")
        st.checkbox("🌬️ **便攜推車靜音小風扇**", value=False, key="gear_hot_1")
        st.checkbox("🧊 **退熱冰涼貼 / 保冷包**", value=False, key="gear_hot_2")
    elif st.session_state.global_temp <= 18.0:
        st.markdown("##### ❄️ 低溫防風保暖裝備 (≤ 18°C)")
        st.checkbox("🧥 **兒童防風禦寒外套**", value=False, key="gear_cold_1")
        st.checkbox("🍼 **暖心溫熱水壺**", value=False, key="gear_cold_2")

    # 5. 依據空氣質素 PM2.5 動態推薦 (預設不勾選)
    if st.session_state.global_pm25 >= 35.0:
        st.markdown("##### 😷 空氣質素護航裝備 (PM2.5 偏高)")
        st.checkbox("😷 **兒童防護口罩 (KN95 / 立體親膚)**", value=False, key="gear_pm_1")
        st.checkbox("🧴 **生理鹽水洗鼻噴霧**", value=False, key="gear_pm_2")

elif st.session_state.current_page == "audio":
    st.markdown('<div class="back-btn">', unsafe_allow_html=True)
    if st.button("← 返回主頁面", key="back_audio"):
        st.session_state.current_page = "menu"
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("""
    <div class="card">
        <h3 style="margin-top:0px; color:#1B5E20;">🔊 多頻率驅蚊驅蟲器</h3>
        <p style="margin-bottom:0; color:#2E7D32;">選擇特定昆蟲頻率，開啟防護後即刻切換背景發聲。</p>
    </div>
    """, unsafe_allow_html=True)

    freq_options = [
        "17.4 kHz - 模擬雄蚊翅聲 (驅避咬人母蚊)",
        "14.8 kHz - 蠓蟲/小咬 (黑翅蕈蚋) 專用",
        "12.5 kHz - 蜂類與飛蟲 警戒頻率"
    ]

    selected_idx = freq_options.index(st.session_state.selected_insect_freq) if st.session_state.selected_insect_freq in freq_options else 0
    freq_choice = st.radio("🎯 請選擇要驅避的昆蟲種類：", freq_options, index=selected_idx)
    st.session_state.selected_insect_freq = freq_choice

    freq_map = {
        "17.4 kHz - 模擬雄蚊翅聲 (驅避咬人母蚊)": 17400,
        "14.8 kHz - 蠓蟲/小咬 (黑翅蕈蚋) 專用": 14800,
        "12.5 kHz - 蜂類與飛蟲 警戒頻率": 12500
    }
    current_hz = freq_map[freq_choice]

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
    <div style="text-align:center; padding:12px; background:#E8F5E9; border-radius:10px; border:1px solid #C8E6C9; margin-top:10px;">
        <p style="font-size:1.1rem; color:#1B5E20; font-weight:bold; margin:0;">
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
    status_str = "🟢 超聲波背景持續防護中..." if st.session_state.audio_active else "🔴 聲波目前未啟動"
    audio_js = audio_js_template.replace("__STATUS_TEXT__", status_str)\
                                .replace("__IS_ACTIVE__", 'true' if st.session_state.audio_active else 'false')\
                                .replace("__CURRENT_HZ__", str(current_hz))

    components.html(audio_js, height=80)

elif st.session_state.current_page == "sos":
    st.markdown('<div class="back-btn">', unsafe_allow_html=True)
    if st.button("← 返回主頁面", key="back_sos"):
        st.session_state.current_page = "menu"
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("""
    <div class="card" style="border-left:5px solid #C62828; background-color:#FFEBEE;">
        <h3 style="margin-top:0px; color:#B71C1C;">🚨 一鍵求救與精準 GPS 定位</h3>
        <p style="color:#C62828; margin-bottom:0;">自動抓取實時經緯度，點擊即可複製求救文字簡訊或直接撥打緊急熱線：</p>
    </div>
    """, unsafe_allow_html=True)

    sos_js_template = """
    <div style="text-align:center; padding:10px; background-color:#FFEBEE; border-radius:10px; border:1px solid #FFCDD2; margin-bottom:12px;">
        <div id="sosGpsStatus" style="font-size:1.05rem; color:#C62828; font-weight:bold;">
            📡 正在連線衛星感應經緯度...
        </div>
    </div>

    <div style="background-color:#FFFFFF; border-radius:12px; padding:16px; border-left:5px solid #C62828; box-shadow:0 2px 10px rgba(0,0,0,0.04); margin-bottom:16px; text-align:center;">
        <button id="copyBtn" onclick="copySosText()" style="width:100%; background-color:#C62828; color:white; font-size:1.2rem; font-weight:bold; padding:14px; border:none; border-radius:10px; cursor:pointer;">
            📋 一鍵複製求救簡訊 (含精確經緯度)
        </button>
        <textarea id="sosTextarea" readonly style="width:100%; height:90px; background-color:#F9F9F9; border-radius:8px; border:1px solid #FFCDD2; padding:10px; font-size:1.0rem; margin-top:10px; box-sizing:border-box;"></textarea>
    </div>

    <div style="display:flex; gap:10px;">
        <a href="tel:999" style="flex:1; text-decoration:none;">
            <div style="background-color:#C62828; color:white; text-align:center; padding:12px; border-radius:10px; font-weight:bold; font-size:1.1rem;">
                📞 撥打 999
            </div>
        </a>
        <a href="tel:110" style="flex:1; text-decoration:none;">
            <div style="background-color:#0277BD; color:white; text-align:center; padding:12px; border-radius:10px; font-weight:bold; font-size:1.1rem;">
                📞 撥打 110
            </div>
        </a>
    </div>

    <script>
        function copySosText() {
            var ta = document.getElementById("sosTextarea");
            ta.select();
            document.execCommand('copy');
            document.getElementById("copyBtn").innerText = "✅ 已複製！請至微信/簡訊貼上發送";
            document.getElementById("copyBtn").style.backgroundColor = "#2E7D32";
        }

        if (navigator.geolocation) {
            navigator.geolocation.getCurrentPosition(function(position) {
                var lat = position.coords.latitude;
                var lon = position.coords.longitude;
                document.getElementById("sosGpsStatus").innerHTML = "✅ 已鎖定 GPS 座標：" + lat.toFixed(5) + ", " + lon.toFixed(5);
                var txt = "【🚨 SOS 求救通報】\\n我當前經緯度： " + lat.toFixed(5) + ", " + lon.toFixed(5) + "\\n地圖位置：https://maps.google.com/?q=" + lat.toFixed(5) + "," + lon.toFixed(5);
                document.getElementById("sosTextarea").value = txt;
            });
        }
    </script>
    """

    components.html(sos_js_template, height=320)