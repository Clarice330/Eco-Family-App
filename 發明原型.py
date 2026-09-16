# -*- coding: utf-8 -*-
"""
🍀 絲野仙蹤 (Eco-Family)
親子綠色呼吸智慧隨行助手

功能：
1. 🗺️ 智慧路線規劃
2. 🎒 隨行裝備
3. 🪰 多頻率驅蚊驅蟲器
4. 🚨 一鍵求救與 GPS 定位
5. 🔍 Kimi AI 動植物識別（固定 kimi-k2.6）

執行：
    streamlit run 發明原型.py

依賴：
    pip install streamlit requests pandas
"""
import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import requests
import urllib.parse
import time
import math
import json
import base64

# ============================================================
# 🔑 Kimi API Key
# ============================================================
KIMI_API_KEY = "sk-NKcBPK2IVcuyy6FPPtxmCKVPsqK2ditGFBhkrfnDF7oYpzCp"

# ============================================================
# 🤖 唯一使用的模型（寫死，無其他選項）
# ============================================================
KIMI_MODEL = "kimi-k2.6"
# ============================================================


# ============================================================
# 頁面設定（必須是第一個 st 命令）
# ============================================================
st.set_page_config(
    page_title="絲野仙蹤 Eco-Family",
    page_icon="🍀",
    layout="centered",
    initial_sidebar_state="collapsed"
)


# ============================================================
# SessionState 初始化
# ============================================================
query_params = st.query_params
if "page" in query_params and query_params["page"]:
    st.session_state.current_page = query_params["page"]

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
if "override_weather" not in st.session_state:
    st.session_state.override_weather = False
if "is_elder_mode" not in st.session_state:
    st.session_state.is_elder_mode = False

if "lat" in query_params and "lon" in query_params:
    try:
        st.session_state.my_lat = float(query_params["lat"])
    except ValueError:
        pass
if "my_lat" not in st.session_state:
    st.session_state.my_lat = 22.1568
if "my_lon" not in st.session_state:
    st.session_state.my_lon = 113.5615

if "audio_active" not in st.session_state:
    st.session_state.audio_active = False
if "selected_insect_freq" not in st.session_state:
    st.session_state.selected_insect_freq = "17.4 kHz - 模擬雄蚊翅聲 (驅避咬人母蚊)"
if "current_page" not in st.session_state:
    st.session_state.current_page = "menu"

# AI 識別狀態
if "identify_result" not in st.session_state:
    st.session_state.identify_result = None
if "identify_history" not in st.session_state:
    st.session_state.identify_history = []
if "last_image_id" not in st.session_state:
    st.session_state.last_image_id = None


# ============================================================
# CSS 樣式
# ============================================================
if st.session_state.is_elder_mode:
    text_scale = "1.45"
    big_btn_text = "1.3rem"
    btn_weight = "500"
else:
    text_scale = "1.0"
    big_btn_text = "1.03rem"
    btn_weight = "400"

css_text = (
    ":root {--text-scale:" + text_scale + ";}"
    """
    .stApp {background-color:#F7FAF8;color:#2C3E50;font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,"Helvetica Neue",Arial,sans-serif;}
    .stApp p,.stApp div,.stApp span,.stApp label,.stApp h1,.stApp h2,.stApp h3,.stApp h4,.stApp h5 {font-size:calc(1rem*var(--text-scale))!important;}
    section[data-testid="stSidebar"] {display:none;}
    div[data-testid="stButton"]{width:100%!important;margin:0 0 16px 0!important;padding:0!important;box-sizing:border-box!important;}
    div[data-testid="stButton"]>button{width:100%!important;background-color:#FFFFFF!important;color:#1B5E20!important;border-radius:16px!important;height:76px!important;min-height:76px!important;max-height:76px!important;box-shadow:0 4px 15px rgba(0,0,0,0.04)!important;border:2px solid #E8F5E9!important;text-align:center!important;font-size:"""
    + big_btn_text +
    """!important;font-weight:""" + btn_weight + """!important;-webkit-font-smoothing:antialiased!important;font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,"Helvetica Neue",Arial,sans-serif!important;margin:0 0 16px 0!important;padding:0 8px!important;transition:all 0.2s ease-in-out!important;display:flex!important;align-items:center!important;justify-content:center!important;text-decoration:none!important;border-bottom:none!important;box-sizing:border-box!important;line-height:1.2!important;}
    div[data-testid="stButton"]>button:hover{border-color:#2E7D32!important;box-shadow:0 6px 20px rgba(46,125,50,0.18)!important;background-color:#F1F8E9!important;transform:translateY(-2px)!important;color:#1B5E20!important;}
    .sos-header-btn button{background-color:#FFEBEE!important;color:#C62828!important;border:1.5px solid #FFCDD2!important;font-weight:700!important;height:38px!important;min-height:38px!important;font-size:0.85rem!important;border-radius:8px!important;padding:4px 8px!important;margin-bottom:0px!important;}
    .audio-header-btn button{height:38px!important;min-height:38px!important;font-size:0.85rem!important;border-radius:8px!important;padding:4px 8px!important;margin-bottom:0px!important;}
    .card{background-color:#FFFFFF;border-radius:12px;padding:18px;box-shadow:0 2px 10px rgba(0,0,0,0.04);border-left:5px solid #2E7D32;border-top:1px solid #E8F5E9;border-right:1px solid #E8F5E9;border-bottom:1px solid #E8F5E9;margin-bottom:16px;}
    .metric-card{background-color:#F1F8E9;border-radius:10px;padding:10px;text-align:center;border:1px solid #C5E1A5;margin-bottom:10px;}
    .metric-title{font-size:calc(0.82rem*var(--text-scale));color:#388E3C;font-weight:bold;}
    .metric-value{font-size:calc(1.35rem*var(--text-scale));font-weight:bold;color:#1B5E20;}
    .badge-green{background-color:#2E7D32;color:white;padding:4px 10px;border-radius:10px;font-size:calc(0.8rem*var(--text-scale));font-weight:bold;}
    .badge-star{background-color:#E65100;color:white;padding:4px 10px;border-radius:10px;font-size:calc(0.8rem*var(--text-scale));font-weight:bold;}
    .badge-sim{background-color:#F57F17;color:white;padding:3px 8px;border-radius:8px;font-size:calc(0.8rem*var(--text-scale));font-weight:bold;}
    .badge-feature{background-color:#0277BD;color:white;padding:2px 8px;border-radius:6px;font-size:calc(0.78rem*var(--text-scale));font-weight:bold;margin-left:4px;}
    .back-btn button{background-color:#E8F5E9!important;color:#1B5E20!important;font-weight:bold!important;padding:8px 16px!important;font-size:calc(0.95rem*var(--text-scale))!important;border-radius:8px!important;border:1px solid #C8E6C9!important;margin-bottom:16px!important;height:auto!important;min-height:auto!important;}
    .history-card{background-color:#FFFFFF;border-radius:10px;padding:12px;border-left:4px solid #0277BD;box-shadow:0 2px 8px rgba(0,0,0,0.03);margin-bottom:10px;}
"""
)
st.markdown(f"<style>{css_text}</style>", unsafe_allow_html=True)


# ============================================================
# 工具函式
# ============================================================
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


def call_kimi_vision(image_bytes, mime_type, system_prompt):
    """
    呼叫 Kimi 視覺模型（固定 kimi-k2.6）進行圖片辨識。
    回傳 (成功?, 內容或錯誤訊息)
    """
    try:
        base64_img = base64.b64encode(image_bytes).decode("utf-8")
        headers = {
            "Authorization": f"Bearer {KIMI_API_KEY.strip()}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": KIMI_MODEL,  # 永遠使用 kimi-k2.6
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": system_prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:{mime_type};base64,{base64_img}"
                            }
                        }
                    ]
                }
            ],
            "temperature": 1
        }
        res = requests.post(
            "https://api.moonshot.cn/v1/chat/completions",
            json=payload,
            headers=headers,
            timeout=60
        )
        if res.status_code == 200:
            data = res.json()
            content = data["choices"][0]["message"]["content"]
            return True, content
        else:
            try:
                err_json = res.json()
            except Exception:
                err_json = {}
            err_msg = err_json.get("error", {}).get("message", res.text)
            return False, f"HTTP {res.status_code}：{err_msg}"
    except requests.exceptions.Timeout:
        return False, "請求逾時，請稍後再試或改用較小的圖片。"
    except requests.exceptions.ConnectionError:
        return False, "無法連線至 Kimi API，請檢查網路。"
    except Exception as e:
        return False, f"未預期錯誤：{str(e)}"


def build_system_prompt(style):
    if "親子" in style:
        style_prompt = "請以親切、富教育意義且適合小朋友聽的生動口吻解說。"
    elif "專業" in style:
        style_prompt = "請以嚴謹的生物學專業角度解說形態特徵、科屬分類與生態習性。"
    else:
        style_prompt = "請重點著重於戶外接觸安全性、是否有毒性/刺針/過敏原，以及緊急處理原則。"
    return (
        f"你是一位專業的野生動植物學家與生態科普專家。{style_prompt}\n"
        "請分析圖片中的動植物或昆蟲，並以下列條理分明的格式輸出：\n"
        "1. 【物種名稱】：中文常用名（拉丁學名）\n"
        "2. 【生態特徵與習性】：外形重點、棲地與生活習性\n"
        "3. 【💡 親子趣聞 / 知識小檔案】：有趣的小知識或故事\n"
        "4. 【⚠️ 戶外安全與防護提示】：是否具毒性、刺針、咬人風險，以及觀察時的注意事項\n"
        "如果圖片中沒有可辨識的動植物，請直接說明「無法從這張圖片辨識出動植物」。"
    )


update_weather_and_aqi()


# ============================================================
# 頂部 Header
# ============================================================
audio_badge_text = "🟢 驅蟲運作" if st.session_state.audio_active else "🔴 驅蟲未啟"
col_head1, col_head2, col_head3 = st.columns([1.5, 0.9, 0.9])
with col_head1:
    st.markdown(
        '<div><div class="brand-title" style="font-size:calc(1.55rem*var(--text-scale));font-weight:bold;color:#1B5E20;">🍀 絲野仙蹤 Eco-Family</div><div class="brand-sub" style="font-size:calc(0.8rem*var(--text-scale));color:#666;">親子綠色呼吸智慧隨行助手</div></div>',
        unsafe_allow_html=True
    )
with col_head2:
    if st.button(f"🔊 {audio_badge_text}", key="top_right_audio_btn"):
        st.session_state.current_page = "audio"
        st.rerun()
with col_head3:
    if st.button("🚨 一鍵求救", key="top_right_sos_btn"):
        st.session_state.current_page = "sos"
        st.rerun()
st.markdown("<hr style='margin-top:5px;margin-bottom:15px;border-color:#E8F5E9;'>", unsafe_allow_html=True)


# ============================================================
# 主選單
# ============================================================
if st.session_state.current_page == "menu":
    elder_toggle = st.toggle("👵 關愛大字體模式 (老年版)", value=st.session_state.is_elder_mode)
    if elder_toggle != st.session_state.is_elder_mode:
        st.session_state.is_elder_mode = elder_toggle
        st.rerun()
    if st.button("🗺️ 智慧路線規劃", key="btn_m1", use_container_width=True):
        st.session_state.current_page = "routes"
        st.rerun()
    if st.button("🎒 隨行裝備", key="btn_m2", use_container_width=True):
        st.session_state.current_page = "gear"
        st.rerun()
    if st.button("🔍 親子生態動植物識別", key="btn_m3", use_container_width=True):
        st.session_state.current_page = "eco_identify"
        st.rerun()


# ============================================================
# 智慧路線規劃
# ============================================================
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
    weather_tag_html = '<span class="badge-sim">🛠️ 手動模擬數據中</span>' if st.session_state.override_weather else '<span style="color:#2E7D32;font-size:0.85rem;font-weight:bold;">(📡 實時連線)</span>'
    st.markdown(f"##### ☁️ 當前氣象數據 {weather_tag_html}", unsafe_allow_html=True)
    r1, r2, r3, r4 = st.columns(4)
    with r1:
        st.markdown(f'<div class="metric-card"><div class="metric-title">🌡️ 氣溫</div><div class="metric-value">{st.session_state.global_temp:.1f}°C</div></div>', unsafe_allow_html=True)
    with r2:
        st.markdown(f'<div class="metric-card"><div class="metric-title">☀️ 紫外線</div><div class="metric-value">UV {st.session_state.global_uv:.1f}</div></div>', unsafe_allow_html=True)
    with r3:
        st.markdown(f'<div class="metric-card"><div class="metric-title">🍃 PM2.5</div><div class="metric-value">{st.session_state.global_pm25:.1f}</div></div>', unsafe_allow_html=True)
    with r4:
        rain_text = "是" if st.session_state.global_rain else "否"
        st.markdown(f'<div class="metric-card"><div class="metric-title">🌧️ 是否降雨</div><div class="metric-value">{rain_text}</div></div>', unsafe_allow_html=True)
    st.write("")
    st.markdown(
        '<div class="card"><h3 style="margin-top:0px;color:#1E5631;">🗺️ 目的地與氣象/設施適應路線規劃</h3><p style="font-size:0.9rem;margin-bottom:0;">選擇目的地並可依據<b>坡度需求、母嬰室設施與當前氣象</b>自動調整評分與推薦：</p></div>',
        unsafe_allow_html=True
    )
    unique_destinations = {
        "大潭山步行徑 (氹仔區)": [
            {"id": 101, "target_condition": "rain", "name": "🌲 大潭山斜行升降機風雨遮陽主線", "shade": 95, "rain_safe": True, "base_crowd": 12, "slope": "平緩 (斜行電梯/無障礙)", "has_nursery": True, "length": "2.2 公里", "time": "40 分鐘", "origin": "113.5615,22.1568", "destination": "113.5630,22.1580", "dest_name": "大潭山斜行升降機", "desc": "【下雨/惡劣天氣專屬推薦】設有無障礙風雨連廊與斜行電梯，設有母嬰洗手間，95% 高樹蔭覆蓋。"},
            {"id": 102, "target_condition": "hot", "name": "🦋 大潭山谷地賞蝶樹蔭林陰密徑", "shade": 90, "rain_safe": False, "base_crowd": 8, "slope": "中等緩坡", "has_nursery": True, "length": "1.8 公里", "time": "35 分鐘", "origin": "113.5615,22.1568", "destination": "113.5620,22.1595", "dest_name": "大潭山郊野公園", "desc": "【高溫/強紫外線專屬推薦】茂密山谷樹蔭天然擋陽，郊野公園內備有母嬰室及休息亭。"},
            {"id": 103, "target_condition": "cool", "name": "☀️ 大潭山山頂瞭望台 360度觀景線", "shade": 45, "rain_safe": False, "base_crowd": 28, "slope": "陡坡攀升", "has_nursery": False, "length": "3.8 公里", "time": "70 分鐘", "origin": "113.5615,22.1568", "destination": "113.5650,22.1610", "dest_name": "大潭山觀察台", "desc": "【晴朗涼爽專屬推薦】直達山頂瞭望台，視野無遮擋，俯瞰全景。"}
        ],
        "松山 (東望洋) 健康徑": [
            {"id": 201, "target_condition": "rain", "name": "🗼 東望洋燈塔與防空洞展館歷史避雨線", "shade": 60, "rain_safe": True, "base_crowd": 30, "slope": "平緩道路", "has_nursery": True, "length": "2.5 公里", "time": "50 分鐘", "origin": "113.5482,22.1965", "destination": "113.5498,22.1968", "dest_name": "東望洋燈塔", "desc": "【下雨天氣專屬推薦】途經松山防空洞展館，可隨時入內避雨，展館內設有母嬰設施。"},
            {"id": 202, "target_condition": "hot", "name": "🌿 松山公園高樹蔭綠亭遮陽漫步線", "shade": 92, "rain_safe": True, "base_crowd": 20, "slope": "平緩道路", "has_nursery": True, "length": "1.2 公里", "time": "25 分鐘", "origin": "113.5482,22.1965", "destination": "113.5488,22.1972", "dest_name": "松山公園", "desc": "【高溫/強紫外線專屬推薦】全線密集高大榕樹掩映，公園洗手間配備母嬰護理台。"},
            {"id": 203, "target_condition": "cool", "name": "🏃‍♂️ 松山環山防滑塑膠跑道親子健身線", "shade": 75, "rain_safe": False, "base_crowd": 55, "slope": "中等緩坡", "has_nursery": False, "length": "1.7 公里", "time": "30 分鐘", "origin": "113.5482,22.1965", "destination": "113.5490,22.1980", "dest_name": "松山跑步徑", "desc": "【晴朗涼爽專屬推薦】熱門運動步道，設有兒童遊樂場與休閒設施。"}
        ],
        "黑沙水庫健康徑 (路環區)": [
            {"id": 301, "target_condition": "rain", "name": "🛶 黑沙水庫水上單車風雨亭線", "shade": 70, "rain_safe": True, "base_crowd": 18, "slope": "平緩道路", "has_nursery": True, "length": "1.0 公里", "time": "25 分鐘", "origin": "113.5682,22.1245", "destination": "113.5688,22.1250", "dest_name": "黑沙水庫水上單車", "desc": "【下雨天氣專屬推薦】設有大型景觀避雨亭，遊客中心內設有育嬰室設施。"},
            {"id": 302, "target_condition": "hot", "name": "💧 黑沙水庫吊橋環湖高蔭氧吧線", "shade": 94, "rain_safe": False, "base_crowd": 10, "slope": "中等緩坡", "has_nursery": True, "length": "1.5 公里", "time": "35 分鐘", "origin": "113.5682,22.1245", "destination": "113.5695,22.1255", "dest_name": "黑沙水庫郊野公園", "desc": "【高溫/強紫外線專屬推薦】濃密樹冠覆蓋湖畔步道，公園服務站備有母嬰室。"},
            {"id": 303, "target_condition": "cool", "name": "🌲 水庫後山原生植物科普攬勝線", "shade": 60, "rain_safe": False, "base_crowd": 8, "slope": "陡坡攀升", "has_nursery": False, "length": "2.0 公里", "time": "45 分鐘", "origin": "113.5682,22.1245", "destination": "113.5700,22.1260", "dest_name": "黑沙水庫植物園", "desc": "【晴朗涼爽專屬推薦】視野良好，沿途標註原生植物科普牌。"}
        ],
        "小潭山 2000 環山徑 (氹仔區)": [
            {"id": 401, "target_condition": "rain", "name": "🌊 小潭山西灣大橋海景風雨涼亭線", "shade": 80, "rain_safe": True, "base_crowd": 14, "slope": "平緩道路", "has_nursery": True, "length": "2.3 公里", "time": "45 分鐘", "origin": "113.5435,22.1521", "destination": "113.5445,22.1530", "dest_name": "小潭山2000環山徑", "desc": "【下雨天氣專屬推薦】沿途涼亭極多，設有無障礙洗手間及母嬰換尿布台。"},
            {"id": 402, "target_condition": "hot", "name": "👶 小潭山無障礙坡道高蔭林陰線", "shade": 91, "rain_safe": True, "base_crowd": 9, "slope": "平緩 (無障礙坡道)", "has_nursery": True, "length": "1.6 公里", "time": "30 分鐘", "origin": "113.5435,22.1521", "destination": "113.5440,22.1528", "dest_name": "小潭山休閒花園", "desc": "【高溫/強紫外線專屬推薦】樹蔭極高，坡道平緩，帶嬰兒車極度舒適，設母嬰室。"},
            {"id": 403, "target_condition": "cool", "name": "⛰️ 小潭山山頂天際線視野縱走線", "shade": 50, "rain_safe": False, "base_crowd": 22, "slope": "陡坡攀升", "has_nursery": False, "length": "3.5 公里", "time": "60 分鐘", "origin": "113.5435,22.1521", "destination": "113.5460,22.1545", "dest_name": "小潭山山頂觀景點", "desc": "【晴朗涼爽專屬推薦】遠眺城市天際線，景致開闊。"}
        ],
        "黑沙龍爪角海岸徑 (路環區)": [
            {"id": 501, "target_condition": "rain", "name": "⛩️ 榕樹灣風雨亭連廊避雨線", "shade": 85, "rain_safe": True, "base_crowd": 15, "slope": "平緩道路", "has_nursery": False, "length": "1.0 公里", "time": "25 分鐘", "origin": "113.5712,22.1098", "destination": "113.5718,22.1102", "dest_name": "榕樹灣風雨亭", "desc": "【下雨天氣專屬推薦】大榕樹群與涼亭避風避雨，安全性高。"},
            {"id": 502, "target_condition": "hot", "name": "🗿 龍爪角竹灣高蔭避暑步道", "shade": 88, "rain_safe": False, "base_crowd": 25, "slope": "中等緩坡", "has_nursery": True, "length": "1.8 公里", "time": "45 分鐘", "origin": "113.5712,22.1098", "destination": "113.5730,22.1120", "dest_name": "竹灣豪園觀景台", "desc": "【高溫/強紫外線專屬推薦】竹林與綠樹擋住海面烈日暴曬，起點設有母嬰設施。"},
            {"id": 503, "target_condition": "cool", "name": "🌊 龍爪角奇石聽濤海岸地質線", "shade": 30, "rain_safe": False, "base_crowd": 60, "slope": "中等緩坡 (部分礁石)", "has_nursery": False, "length": "1.2 公里", "time": "40 分鐘", "origin": "113.5712,22.1098", "destination": "113.5725,22.1110", "dest_name": "龍爪角海岸徑", "desc": "【晴朗涼爽專屬推薦】沿海奇石，聽濤觀海，晴天無浪時極致震撼。"}
        ],
        "望廈山市政公園步道": [
            {"id": 601, "target_condition": "rain", "name": "🌺 望廈山溫室展館室內避雨線", "shade": 95, "rain_safe": True, "base_crowd": 12, "slope": "平緩道路", "has_nursery": True, "length": "0.8 公里", "time": "20 分鐘", "origin": "113.5488,22.2062", "destination": "113.5490,22.2065", "dest_name": "望廈山溫室展館", "desc": "【下雨天氣專屬推薦】室內溫室展示花卉，下雨天不濕身，設有標準母嬰室。"},
            {"id": 602, "target_condition": "hot", "name": "🌿 望廈山茂密綠林避暑步道", "shade": 92, "rain_safe": True, "base_crowd": 16, "slope": "平緩道路", "has_nursery": True, "length": "1.1 公里", "time": "30 分鐘", "origin": "113.5488,22.2062", "destination": "113.5495,22.2070", "dest_name": "望廈山市政公園", "desc": "【高溫/強紫外線專屬推薦】市區高覆蓋天然綠肺遮陽，公園處備有母嬰育嬰間。"},
            {"id": 603, "target_condition": "cool", "name": "🏃‍♂️ 望廈山砲台古蹟文化攬勝線", "shade": 70, "rain_safe": False, "base_crowd": 20, "slope": "中等緩坡", "has_nursery": False, "length": "1.5 公里", "time": "35 分鐘", "origin": "113.5488,22.2062", "destination": "113.5500,22.2075", "dest_name": "望廈砲台", "desc": "【晴朗涼爽專屬推薦】歷史文化古蹟步道，展望北區城市景觀。"}
        ]
    }
    col_sel1, col_sel2 = st.columns([2, 1])
    with col_sel1:
        selected_dest = st.selectbox("📍 請選擇目的地：", list(unique_destinations.keys()))
    with col_sel2:
        selected_slope = st.selectbox("🏔️ 坡度篩選：", ["全部坡度", "平緩 (無障礙/推車友善)", "中等緩坡", "陡坡攀升"])
    need_nursery = st.checkbox("🍼 僅顯示設有母嬰室 / 育嬰設施之路線", value=False)
    cur_temp = st.session_state.global_temp
    cur_uv = st.session_state.global_uv
    is_rain = st.session_state.global_rain
    dest_routes = unique_destinations[selected_dest]
    time_seed = int(time.time() / 8)
    if is_rain:
        st.info("🌧️ 檢測到降雨氣象！系統已為您優先推薦【風雨遮陽 / 室內避雨路線】。")
    elif cur_temp >= 26.0 or cur_uv >= 2.5:
        st.info("☀️ 檢測到高溫/強紫外線氣象！系統已為您優先推薦【高樹蔭覆蓋林陰避暑路線】。")
    else:
        st.success("🌤️ 當前氣象晴朗宜人！系統已為您優先推薦【山頂展望 / 景觀視野路線】。")
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
    st.markdown(f"#### 🎯 當前條件篩選推薦路線 ({len(sorted_dest_routes)} 條)：")
    if not sorted_dest_routes:
        st.warning("⚠️ 目前選取的目的地無符合坡度或母嬰室篩選條件之路線，請嘗試放寬篩選條件。")
    for idx, route in enumerate(sorted_dest_routes):
        is_best = (idx == 0)
        badge = '<span class="badge-star">🌟 當前最佳推薦</span>' if is_best else f'<span class="badge-green">適應分: {route["dynamic_score"]}</span>'
        nursery_badge = '<span class="badge-feature">🍼 設母嬰室</span>' if route["has_nursery"] else ''
        nav_url = f"https://uri.amap.com/navigation?from={route['origin']},Start&to={route['destination']},{urllib.parse.quote(route['dest_name'])}&mode=walk&policy=1&src=mypage&callnative=1"
        bg_style = "border-left:6px solid #E65100;background-color:#FFFDE7;" if is_best else ""
        st.markdown(
            f'''
<div class="card" style="{bg_style}">
    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:6px;">
        <h4 style="margin:0;color:#1B5E20;font-size:1.15rem;">{route['name']} {nursery_badge}</h4>
        {badge}
    </div>
    <p style="font-size:0.88rem;color:#555;margin-bottom:8px;">{route['desc']}</p>
    <div style="font-size:0.83rem;color:#333;line-height:1.6;margin-bottom:12px;">
        <b>📏 長度：</b>{route['length']} | <b>⏱️ 時間：</b>{route['time']} | <b>⛰️ 坡度：</b><b style="color:#0277BD;">{route['slope']}</b><br/>
        <b>🌳 樹蔭：</b>{route['shade']}% | <b>🚶‍♂️ 實時人數：</b><b style="color:#EF6C00;">{route['live_crowd']} 人</b>
    </div>
    <a href="{nav_url}" target="_blank" style="text-decoration:none;">
        <div style="background-color:#1B5E20;color:white;text-align:center;padding:10px;border-radius:8px;font-weight:bold;font-size:0.95rem;">🧭 開啟路線地圖導航</div>
    </a>
</div>
''',
            unsafe_allow_html=True
        )


# ============================================================
# 隨行裝備
# ============================================================
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
    weather_tag_html = '<span class="badge-sim">🛠️ 手動模擬數據中</span>' if st.session_state.override_weather else '<span style="color:#2E7D32;font-size:0.85rem;font-weight:bold;">(📡 實時連線)</span>'
    st.markdown(f"##### ☁️ 當前氣象數據 {weather_tag_html}", unsafe_allow_html=True)
    r1, r2, r3, r4 = st.columns(4)
    with r1:
        st.markdown(f'<div class="metric-card"><div class="metric-title">🌡️ 氣溫</div><div class="metric-value">{st.session_state.global_temp:.1f}°C</div></div>', unsafe_allow_html=True)
    with r2:
        st.markdown(f'<div class="metric-card"><div class="metric-title">☀️ 紫外線</div><div class="metric-value">UV {st.session_state.global_uv:.1f}</div></div>', unsafe_allow_html=True)
    with r3:
        st.markdown(f'<div class="metric-card"><div class="metric-title">🍃 PM2.5</div><div class="metric-value">{st.session_state.global_pm25:.1f}</div></div>', unsafe_allow_html=True)
    with r4:
        rain_text = "是" if st.session_state.global_rain else "否"
        st.markdown(f'<div class="metric-card"><div class="metric-title">🌧️ 是否降雨</div><div class="metric-value">{rain_text}</div></div>', unsafe_allow_html=True)
    st.write("")
    st.markdown(
        '<div class="card"><h3 style="margin-top:0px;color:#1E5631;">🎒 當前氣象動態推薦隨行裝備</h3><p style="font-size:0.9rem;margin-bottom:0;">系統根據目前的<b>氣溫、紫外線、是否降雨與懸浮微粒</b>數據精算出的推薦清單 (請依需求勾選完成)：</p></div>',
        unsafe_allow_html=True
    )
    st.markdown("##### 📌 出行必備基礎裝備")
    st.checkbox("🍼 **兒童水壺 / 保溫杯** (隨時補充水分)", value=False, key="gear_water")
    st.checkbox("🧻 **濕紙巾與消毒個人用品**", value=False, key="gear_wipes")
    st.checkbox("🩹 **隨身創可貼與急救盒**", value=False, key="gear_firstaid")
    if st.session_state.global_rain:
        st.markdown("##### 🌧️ 是否降雨：當前降雨專屬裝備")
        st.checkbox("🌧️ **嬰兒車透氣防雨罩 & 親子大雨傘**", value=False, key="gear_rain1")
        st.checkbox("🌂 **備用寶寶乾爽衣物 1 套 (防水袋裝)**", value=False, key="gear_rain2")
        st.checkbox("👟 **兒童防滑雨鞋**", value=False, key="gear_rain3")
    cur_uv = st.session_state.global_uv
    if cur_uv >= 2.5:
        st.markdown(f"##### ☀️ 防曬護膚專屬裝備 (當前 UV {cur_uv:.1f} 偏強)")
        st.checkbox("☀️ **兒童高效防曬乳 (SPF50+)**", value=False, key="gear_uv_high1")
        st.checkbox("🧢 **推車抗 UV 遮陽罩 & 親子大簷太陽帽**", value=False, key="gear_uv_high2")
        st.checkbox("🕶️ **兒童太陽眼鏡**", value=False, key="gear_uv_high3")
    cur_t = st.session_state.global_temp
    if cur_t >= 26.0:
        st.markdown(f"##### 🌡️ 高溫防暑專屬裝備 (當前 {cur_t:.1f}°C 偏熱)")
        st.checkbox("🌬️ **夾式推車靜音小風扇** *(防止寶寶高溫中暑)*", value=False, key="gear_temp_hot1")
        st.checkbox("🧊 **兒童退熱貼 / 電解質水補給包**", value=False, key="gear_temp_hot2")
    elif cur_t <= 20.0:
        st.markdown(f"##### 🧥 保暖防風專屬裝備 (當前 {cur_t:.1f}°C 偏涼)")
        st.checkbox("🧥 **兒童保暖防風外套 & 小毛毯**", value=False, key="gear_temp_cold1")
        st.checkbox("☕ **熱水保溫壺**", value=False, key="gear_temp_cold2")
    cur_pm25 = st.session_state.global_pm25
    if cur_pm25 >= 15.0:
        st.markdown(f"##### 😷 懸浮微粒：呼吸道護理裝備 (當前 PM2.5 {cur_pm25:.1f})")
        st.checkbox("😷 **兒童高防護透氣口罩**", value=False, key="gear_pm_high")


# ============================================================
# 驅蟲頁
# ============================================================
elif st.session_state.current_page == "audio":
    st.markdown('<div class="back-btn">', unsafe_allow_html=True)
    if st.button("← 返回主頁面", key="back_audio"):
        st.session_state.current_page = "menu"
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="card"><h3 style="margin-top:0px;color:#1E5631;">🪰 多頻率驅蚊驅蟲器</h3><p style="font-size:0.9rem;margin-bottom:0;">選擇特定昆蟲頻率，啟動後離開此頁面聲波依然保持播放。</p></div>',
        unsafe_allow_html=True
    )
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
    st.markdown(
        f'<div class="card" style="text-align:center;"><h2 style="color:#2E7D32;font-size:2.1rem;margin:0;">{current_hz/1000:.1f} kHz</h2><p style="font-size:0.85rem;color:#666;margin-top:4px;">選擇頻率：<b>{freq_choice.split("-")[1].strip()}</b></p></div>',
        unsafe_allow_html=True
    )
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

    audio_html = """
<div style="text-align:center;padding:10px;background:#F1F8E9;border-radius:10px;">
    <p style="font-size:0.9rem;color:#2E7D32;font-weight:bold;margin:0;">__STATUS__</p>
</div>
<script>
let actx=null;let osc=null;
if(__IS_ON__){
try{
actx=new(window.AudioContext||window.webkitAudioContext)();
osc=actx.createOscillator();
let g=actx.createGain();
osc.type='sine';
osc.frequency.setValueAtTime(__HZ__,actx.currentTime);
g.gain.setValueAtTime(0.12,actx.currentTime);
osc.connect(g);g.connect(actx.destination);
osc.start();
}catch(e){}
}
</script>
    """
    status_str = "🟢 超聲波背景持續播放中..." if st.session_state.audio_active else "🔴 聲波目前未啟動"
    audio_html = audio_html.replace("__STATUS__", status_str)
    audio_html = audio_html.replace("__IS_ON__", "true" if st.session_state.audio_active else "false")
    audio_html = audio_html.replace("__HZ__", str(current_hz))
    components.html(audio_html, height=80)


# ============================================================
# SOS 求救頁
# ============================================================
elif st.session_state.current_page == "sos":
    st.markdown('<div class="back-btn">', unsafe_allow_html=True)
    if st.button("← 返回主頁面", key="back_sos"):
        st.session_state.current_page = "menu"
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="card" style="border-left:5px solid #C62828;background-color:#FFEBEE;"><h3 style="margin-top:0px;color:#B71C1C;">🚨 一鍵求救與精準 GPS 定位通報</h3><p style="font-size:0.9rem;color:#C62828;margin-bottom:0;">如在戶外遇到緊急情況，請保持冷靜。系統已自動獲取您的 GPS 並比對地區緊急求救熱線：</p></div>',
        unsafe_allow_html=True
    )
    sos_html = """
<div style="text-align:center;padding:10px;background-color:#FFEBEE;border-radius:10px;border:1px solid #FFCDD2;margin-bottom:12px;">
    <div id="sosGpsStatus" style="font-size:0.9rem;color:#C62828;font-weight:bold;margin-bottom:6px;">📡 正在感應當前衛星精確一鍵求救 GPS 座標...</div>
    <div id="regionNotice" style="font-size:0.85rem;color:#B71C1C;font-weight:bold;"></div>
</div>
<div style="background-color:#FFFFFF;border-radius:12px;padding:16px;border-left:5px solid #C62828;box-shadow:0 2px 10px rgba(0,0,0,0.04);margin-bottom:16px;text-align:center;">
    <h4 style="color:#C62828;margin-top:0;font-size:1.05rem;">📋 一鍵複製精準 GPS 求救簡訊內容</h4>
    <div style="margin-bottom:12px;">
        <button id="copyBtn" onclick="copySosText()" style="width:100%;background-color:#C62828;color:white;font-size:1.1rem;font-weight:bold;padding:14px;border:none;border-radius:10px;cursor:pointer;box-shadow:0 4px 10px rgba(198,40,40,0.3);">📋 一鍵複製求救簡訊內容 (含實時經緯度)</button>
    </div>
    <p style="font-size:0.85rem;color:#666;text-align:left;margin-bottom:4px;font-weight:bold;">📱 將複製的內文貼至微信、簡訊發送給救援隊：</p>
    <textarea id="sosTextarea" readonly style="width:100%;height:140px;background-color:#F9F9F9;border-radius:8px;border:1px solid #FFCDD2;padding:10px;font-family:monospace;font-size:0.85rem;box-sizing:border-box;color:#333;"></textarea>
</div>
<div id="phoneArea" style="margin-bottom:16px;">
    <h5 style="margin-bottom:8px;color:#1B5E20;">📞 求助熱線直撥</h5>
    <div style="display:flex;gap:10px;">
        <a href="tel:999" style="flex:1;text-decoration:none;"><div style="background-color:#0277BD;color:white;text-align:center;padding:12px;border-radius:10px;font-weight:bold;">📞 999</div></a>
        <a href="tel:110" style="flex:1;text-decoration:none;"><div style="background-color:#C62828;color:white;text-align:center;padding:12px;border-radius:10px;font-weight:bold;">📞 110</div></a>
        <a href="tel:120" style="flex:1;text-decoration:none;"><div style="background-color:#EF6C00;color:white;text-align:center;padding:12px;border-radius:10px;font-weight:bold;">📞 120</div></a>
    </div>
</div>
<script>
let gpsLat=null;let gpsLon=null;
const statusEl=document.getElementById("sosGpsStatus");
const noticeEl=document.getElementById("regionNotice");
const taEl=document.getElementById("sosTextarea");
if(navigator.geolocation){
navigator.geolocation.getCurrentPosition(function(pos){
gpsLat=pos.coords.latitude.toFixed(5);
gpsLon=pos.coords.longitude.toFixed(5);
const acc=pos.coords.accuracy.toFixed(0);
statusEl.innerText="✅ GPS定位成功";
noticeEl.innerText=`定位精度約${acc}公尺，緯度${gpsLat}，經度${gpsLon}`;
const googleMapUrl = `https://www.google.com/maps?q=${gpsLat},${gpsLon}`;
taEl.value = `緊急求助！本人遇險需要救援。\\n緯度：${gpsLat}\\n經度：${gpsLon}\\nGoogle Maps位置連結：${googleMapUrl}\\n請盡快前來救援！`;
},function(err){
statusEl.innerText="❌ GPS定位失敗，請開啟定位權限";
taEl.value="緊急求助！無法獲取GPS，請協助救援！";
});
}else{
statusEl.innerText="❌ 瀏覽器不支援GPS定位";
taEl.value="緊急求助！無法獲取GPS，請協助救援！";
}
function copySosText(){taEl.select();document.execCommand('copy');alert("✅ 求救訊息已複製！");}
</script>
    """
    components.html(sos_html, height=860)


# ============================================================
# 🔍 Kimi AI 動植物識別（固定 kimi-k2.6）
# ============================================================
elif st.session_state.current_page == "eco_identify":
    st.markdown('<div class="back-btn">', unsafe_allow_html=True)
    if st.button("← 返回主頁面", key="back_identify"):
        st.session_state.current_page = "menu"
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown(f"""
    <div class="card">
        <h3 style="margin-top:0px; color:#1B5E20;">🔍 Kimi AI 親子生態動植物智慧識別</h3>
        <p style="margin-bottom:0; color:#2E7D32;">現場拍照或上傳照片，即時辨識戶外常見的動植物與昆蟲！</p>
        <p style="margin:6px 0 0 0; color:#888; font-size:0.75rem;">模型：{KIMI_MODEL}</p>
    </div>
    """, unsafe_allow_html=True)

    prompt_style = st.selectbox(
        "🎨 選擇解說風格：",
        ["🌱 親子科普故事模式", "🔬 專業生物圖鑑模式", "⚠️ 戶外安全與毒性檢查"],
        index=0,
        key="eco_prompt_style"
    )

    tab_upload, tab_camera = st.tabs(["📁 上傳照片", "📷 現場拍照"])
    img_file = None
    image_id = None

    with tab_upload:
        uploaded = st.file_uploader(
            "選擇相冊中的動植物照片",
            type=["jpg", "jpeg", "png", "webp"],
            key="eco_upload_tab"
        )
        if uploaded:
            img_file = uploaded
            image_id = f"upload_{uploaded.name}_{uploaded.size}"

    with tab_camera:
        captured = st.camera_input("直接拍攝動植物", key="eco_camera_tab")
        if captured:
            img_file = captured
            image_id = f"camera_{captured.size}"

    if img_file is not None:
        st.image(img_file, caption="待識別圖像預覽", use_container_width=True)

        if st.session_state.last_image_id != image_id:
            st.session_state.last_image_id = image_id
            st.session_state.identify_result = None

        if st.button("🤖 開始識別", key="btn_do_identify", use_container_width=True):
            with st.spinner("🌿 Kimi AI 正在分析動植物特徵並生成生態科普說明..."):
                img_bytes = img_file.getvalue()
                mime_type = img_file.type if img_file.type else "image/jpeg"
                system_prompt = build_system_prompt(prompt_style)

                ok, result = call_kimi_vision(
                    image_bytes=img_bytes,
                    mime_type=mime_type,
                    system_prompt=system_prompt
                )

                if ok:
                    st.session_state.identify_result = result
                    st.session_state.identify_history.insert(0, {
                        "style": prompt_style,
                        "model": KIMI_MODEL,
                        "content": result
                    })
                    st.session_state.identify_history = st.session_state.identify_history[:10]
                    st.success("🎉 識別成功！")
                    st.rerun()
                else:
                    st.error(f"❌ 識別失敗：{result}")

    if st.session_state.identify_result:
        st.markdown("""
        <div class="card" style="border-left:5px solid #2E7D32; background-color:#F1F8E9;">
            <h4 style="margin-top:0; color:#1B5E20;">🌿 Kimi AI 生態辨識結果</h4>
        </div>
        """, unsafe_allow_html=True)
        st.markdown(st.session_state.identify_result)

        st.download_button(
            "💾 下載辨識結果 (.txt)",
            data=st.session_state.identify_result,
            file_name="動植物辨識結果.txt",
            mime="text/plain",
            use_container_width=True,
            key="download_identify_result"
        )

    if st.session_state.identify_history:
        with st.expander(f"📚 辨識歷史紀錄（最近 {len(st.session_state.identify_history)} 筆）", expanded=False):
            if st.button("🗑️ 清空歷史紀錄", key="clear_identify_history"):
                st.session_state.identify_history = []
                st.session_state.identify_result = None
                st.rerun()

            for i, item in enumerate(st.session_state.identify_history):
                preview = item["content"][:200] + ("..." if len(item["content"]) > 200 else "")
                st.markdown(
                    f"""
<div class="history-card">
    <div style="font-size:0.8rem;color:#0277BD;font-weight:bold;margin-bottom:4px;">
        #{i+1} ｜ {item['style']} ｜ 模型：{item['model']}
    </div>
    <div style="font-size:0.88rem;color:#333;white-space:pre-wrap;">{preview}</div>
</div>
""",
                    unsafe_allow_html=True
                )