      
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
6. 📍 共享定位房間（建立/加入房間，地圖即時顯示成員名字與位置）

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
import html
import secrets
import uuid

# ============================================================
# 🔑 Kimi API Key —— 由 st.secrets 讀取（不再寫死在程式碼中）
# ------------------------------------------------------------
# 本地執行：在專案資料夾建立 .streamlit/secrets.toml，內容：
#     KIMI_API_KEY = "你的金鑰"
# 雲端執行（Streamlit Community Cloud）：在 App 的「Settings → Secrets」加入同名設定。
# 未設定時，AI 識別功能會顯示引導提示，其他功能不受影響。
# ============================================================
try:
    KIMI_API_KEY = st.secrets["KIMI_API_KEY"]
except Exception:
    KIMI_API_KEY = ""

# ============================================================
# 🤖 唯一使用的模型（寫死，無其他選項）
# ============================================================
KIMI_MODEL = "kimi-k2.6"
# ============================================================

# ============================================================
# 🔥 Firebase Web 配置（共享定位房間功能用）★ 需自行填入 ★
# ------------------------------------------------------------
# 共享定位需要一個免費的 Firebase Realtime Database（用 Google 帳號即可建立）：
#   ① 前往 https://console.firebase.google.com 建立專案（Spark 免費方案）
#   ② 建立 Realtime Database，並貼上《共享定位房間部署指南.md》中的安全規則
#   ③ 專案設定 → 一般 →「你的應用程式」新增 Web 應用程式，取得「Web API Key」
#   ④ 在 Realtime Database 頁面取得資料庫網址（databaseURL）
# 把下面兩個常數換成你自己的值即可啟用。這組 Web 配置本來就設計為可公開，
# 安全由資料庫安全規則把關。未設定前，「共享定位房間」頁會顯示引導說明，
# 其他功能完全不受影響。詳細圖文步驟請見《共享定位房間部署指南.md》。
# ============================================================
FIREBASE_API_KEY = "AIzaSyDkCFr-N3syeX5_cOLwVMyxEA_cuEH1ZYc"
FIREBASE_DATABASE_URL = "https://eco-family-location-default-rtdb.asia-southeast1.firebasedatabase.app"

# 房間碼字元表：4 位英數字，已剔除易混淆的 0、1、I、O
SL_CODE_ALPHABET = "23456789ABCDEFGHJKMNPQRSTUVWXYZ"

# Firebase 是否已完成設定（未設定時房間頁僅顯示引導，不渲染地圖）
FIREBASE_CONFIGURED = (
    FIREBASE_API_KEY != "PUT_YOUR_FIREBASE_WEB_API_KEY_HERE"
    and FIREBASE_DATABASE_URL != "https://PUT_YOUR_FIREBASE_RTDB_URL_HERE"
)


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

# 邀請連結支援：?page=share_location&room=XXXX 點開後自動帶入房間碼
if "room" in query_params and query_params.get("page") == "share_location":
    linked_room = str(query_params["room"]).strip().upper()
    if len(linked_room) == 4 and all(ch in SL_CODE_ALPHABET for ch in linked_room):
        st.session_state.sl_room_code = linked_room
        st.session_state.sl_uid = ""  # 進入「待加入」流程：先輸入名字再進房
    st.query_params.clear()  # 消化完邀請參數即清空，避免離開後被舊連結反覆拉回

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

# 共享定位房間狀態
if "sl_nickname" not in st.session_state:
    st.session_state.sl_nickname = ""
if "sl_room_code" not in st.session_state:
    st.session_state.sl_room_code = ""
if "sl_uid" not in st.session_state:
    st.session_state.sl_uid = ""
if "sl_role" not in st.session_state:
    st.session_state.sl_role = ""

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
    btn_height = "92px"
else:
    text_scale = "1.0"
    big_btn_text = "1.03rem"
    btn_weight = "400"
    btn_height = "78px"

css_text = (
    "@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+TC:wght@400;500;700;900&display=swap');"
    ":root {--text-scale:" + text_scale + ";}"
    """
    :root{--ef-primary:#1B5E20;--ef-green:#2E7D32;--ef-lime:#7CB342;--ef-mint:#E8F5E9;--ef-mint2:#F1F8E9;--ef-ink:#223327;--ef-ink-soft:#5B6B60;--ef-line:#DCEEDF;--ef-radius:18px;--ef-shadow:0 6px 22px rgba(27,94,32,.08);--ef-shadow-hover:0 14px 34px rgba(27,94,32,.16);}
    .stApp{background:radial-gradient(1100px 420px at 50% -12%,#E3F2E6 0%,rgba(247,250,248,0) 62%),linear-gradient(180deg,#F7FAF8 0%,#F2F8F3 100%);color:var(--ef-ink);font-family:'Noto Sans TC',-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,"Helvetica Neue",Arial,sans-serif;}
    .stApp p,.stApp div,.stApp span,.stApp label{font-size:calc(1rem*var(--text-scale))!important;}
    .stApp h1{font-size:calc(1.75rem*var(--text-scale))!important;font-weight:800;color:var(--ef-primary);}
    .stApp h2{font-size:calc(1.5rem*var(--text-scale))!important;font-weight:800;color:var(--ef-primary);}
    .stApp h3{font-size:calc(1.28rem*var(--text-scale))!important;font-weight:700;color:#1E5631;}
    .stApp h4{font-size:calc(1.1rem*var(--text-scale))!important;font-weight:700;color:#1E5631;}
    .stApp h5{font-size:calc(1rem*var(--text-scale))!important;font-weight:600;color:#1E5631;}
    section[data-testid="stSidebar"]{display:none;}
    #MainMenu{visibility:hidden;}
    [data-testid="stAppDeployButton"]{display:none!important;}
    footer{visibility:hidden;}
    ::-webkit-scrollbar{width:10px;}
    ::-webkit-scrollbar-track{background:transparent;}
    ::-webkit-scrollbar-thumb{background:#C8E6C9;border-radius:999px;border:2px solid #F7FAF8;}
    ::-webkit-scrollbar-thumb:hover{background:#A5D6A7;}
    .brand-wrap{display:flex;align-items:center;gap:10px;}
    .brand-logo{width:44px;height:44px;border-radius:14px;background:linear-gradient(135deg,#2E7D32,#7CB342);display:flex;align-items:center;justify-content:center;box-shadow:0 4px 12px rgba(46,125,50,.28);flex:none;}
    .stApp .brand-logo{font-size:calc(1.5rem*var(--text-scale))!important;}
    .stApp .brand-title{font-size:calc(1.32rem*var(--text-scale))!important;font-weight:900;color:var(--ef-primary);letter-spacing:.02em;}
    .stApp .brand-sub{font-size:calc(0.78rem*var(--text-scale))!important;color:var(--ef-ink-soft);margin-top:1px;}
    .ef-divider{height:3px;border-radius:999px;background:linear-gradient(90deg,rgba(46,125,50,0),rgba(46,125,50,.32) 18%,rgba(124,179,66,.6) 50%,rgba(46,125,50,.32) 82%,rgba(46,125,50,0));margin:12px 0 18px;}
    .hero{position:relative;background:linear-gradient(135deg,#14491B 0%,#1B5E20 42%,#2E7D32 78%,#388E3C 100%);border-radius:22px;padding:32px 22px 24px;text-align:center;color:#FFFFFF;box-shadow:0 14px 36px rgba(27,94,32,.28);overflow:hidden;margin-bottom:20px;}
    .hero::before{content:"";position:absolute;inset:0;background:radial-gradient(280px 150px at 85% 12%,rgba(255,255,255,.16) 0%,rgba(255,255,255,0) 70%),radial-gradient(240px 140px at 10% 90%,rgba(124,179,66,.35) 0%,rgba(124,179,66,0) 70%);pointer-events:none;}
    .hero-deco{position:absolute;font-size:1.25rem;opacity:.45;}
    .hero-deco-1{right:18px;top:14px;}
    .hero-deco-2{right:44px;bottom:12px;}
    .hero-emoji{margin-bottom:10px;filter:drop-shadow(0 4px 8px rgba(0,0,0,.18));line-height:1;}
    .stApp .hero-emoji{font-size:calc(2.6rem*var(--text-scale))!important;}
    .stApp .hero-title{font-size:calc(1.8rem*var(--text-scale))!important;font-weight:900;letter-spacing:.08em;color:#FFFFFF;text-shadow:0 2px 12px rgba(0,0,0,.22);}
    .stApp .hero-title-en{font-size:calc(0.78rem*var(--text-scale))!important;letter-spacing:.42em;text-transform:uppercase;color:#DCEDC8;font-weight:500;margin-top:3px;}
    .stApp .hero-sub{font-size:calc(0.9rem*var(--text-scale))!important;color:#E8F5E9;margin-top:9px;}
    .hero-chips{display:flex;flex-wrap:wrap;gap:8px;justify-content:center;margin-top:15px;position:relative;}
    .stApp .hero-chip{background:rgba(255,255,255,.15);border:1px solid rgba(255,255,255,.28);color:#F1F8E9;border-radius:999px;padding:4px 12px;font-size:calc(0.76rem*var(--text-scale))!important;font-weight:500;}
    div[data-testid="stButton"]{width:100%!important;margin:0 0 14px 0!important;padding:0!important;box-sizing:border-box!important;}
    div[data-testid="stButton"]>button{width:100%!important;background:linear-gradient(135deg,#FFFFFF 0%,#F4FAF5 100%)!important;color:#1B5E20!important;border-radius:16px!important;height:""" + btn_height + """!important;min-height:""" + btn_height + """!important;max-height:""" + btn_height + """!important;box-shadow:0 4px 16px rgba(27,94,32,.06)!important;border:1.5px solid var(--ef-line)!important;text-align:center!important;font-size:""" + big_btn_text + """!important;font-weight:""" + btn_weight + """!important;-webkit-font-smoothing:antialiased!important;font-family:'Noto Sans TC',-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,"Helvetica Neue",Arial,sans-serif!important;margin:0 0 14px 0!important;padding:0 8px!important;transition:all .22s cubic-bezier(.2,.7,.3,1)!important;display:flex!important;align-items:center!important;justify-content:center!important;text-decoration:none!important;border-bottom:none!important;box-sizing:border-box!important;line-height:1.2!important;}
    div[data-testid="stButton"]>button:hover{border-color:#81C784!important;box-shadow:0 10px 26px rgba(46,125,50,.15)!important;background:linear-gradient(135deg,#F1F8E9 0%,#E8F5E9 100%)!important;transform:translateY(-3px)!important;color:#0F3D14!important;}
    div[data-testid="stButton"]>button:active{transform:translateY(-1px) scale(.995)!important;}
    .sos-header-btn button{background:linear-gradient(135deg,#C62828,#E53935)!important;color:#FFFFFF!important;font-weight:700!important;height:40px!important;min-height:40px!important;font-size:calc(0.85rem*var(--text-scale))!important;border-radius:999px!important;padding:4px 14px!important;margin-bottom:0px!important;border:none!important;box-shadow:0 3px 10px rgba(198,40,40,.25)!important;transition:all .2s ease!important;}
    .sos-header-btn button:hover{transform:translateY(-2px)!important;box-shadow:0 6px 18px rgba(198,40,40,.35)!important;}
    .audio-header-btn button{background:linear-gradient(135deg,#FFFFFF,#F1F8E9)!important;color:#2E7D32!important;font-weight:600!important;height:40px!important;min-height:40px!important;font-size:calc(0.85rem*var(--text-scale))!important;border-radius:999px!important;padding:4px 14px!important;margin-bottom:0px!important;border:1.5px solid var(--ef-line)!important;box-shadow:0 3px 10px rgba(27,94,32,.08)!important;transition:all .2s ease!important;}
    .audio-header-btn button:hover{transform:translateY(-2px)!important;border-color:#81C784!important;box-shadow:0 6px 16px rgba(46,125,50,.18)!important;}
    .back-btn button{background:linear-gradient(135deg,#FFFFFF,#F1F8E9)!important;color:#1B5E20!important;font-weight:700!important;padding:9px 20px 9px 16px!important;font-size:calc(0.95rem*var(--text-scale))!important;border-radius:999px!important;border:1.5px solid #C8E6C9!important;margin-bottom:18px!important;box-shadow:0 3px 10px rgba(27,94,32,.08)!important;transition:all .2s ease!important;height:auto!important;min-height:auto!important;}
    .back-btn button:hover{transform:translateX(-4px)!important;border-color:#81C784!important;box-shadow:0 6px 16px rgba(46,125,50,.16)!important;background:linear-gradient(135deg,#F1F8E9,#E8F5E9)!important;}
    .card{position:relative;overflow:hidden;background:#FFFFFF;border-radius:var(--ef-radius);padding:20px 22px;box-shadow:var(--ef-shadow);border:1px solid var(--ef-line);margin-bottom:18px;transition:box-shadow .25s ease,transform .25s ease;}
    .card:hover{box-shadow:var(--ef-shadow-hover);}
    .card::before{content:"";position:absolute;top:0;left:0;right:0;height:4px;background:linear-gradient(90deg,#2E7D32,#7CB342,rgba(124,179,66,0));}
    .card[style*="E65100"]::before{background:linear-gradient(90deg,#E65100,#FFB300,rgba(255,179,0,0));}
    .card[style*="C62828"]::before{background:linear-gradient(90deg,#C62828,#EF5350,rgba(239,83,80,0));}
    .metric-card{background:linear-gradient(180deg,#FFFFFF 0%,#F6FBF6 100%);border-radius:14px;padding:14px 8px;text-align:center;border:1px solid #D9ECD9;margin-bottom:12px;box-shadow:0 3px 10px rgba(27,94,32,.05);transition:all .22s ease;}
    .metric-card:hover{transform:translateY(-3px);box-shadow:0 10px 22px rgba(46,125,50,.13);border-color:#A5D6A7;}
    .stApp .metric-title{font-size:calc(0.82rem*var(--text-scale))!important;color:#388E3C;font-weight:700;letter-spacing:.02em;}
    .stApp .metric-value{font-size:calc(1.3rem*var(--text-scale))!important;font-weight:800;color:var(--ef-primary);margin-top:2px;}
    .stApp .badge-green{background:linear-gradient(135deg,#2E7D32,#43A047);color:#FFFFFF;padding:5px 12px;border-radius:999px;font-size:calc(0.78rem*var(--text-scale))!important;font-weight:700;box-shadow:0 3px 8px rgba(46,125,50,.25);white-space:nowrap;display:inline-block;}
    .stApp .badge-star{background:linear-gradient(135deg,#E65100,#FB8C00);color:#FFFFFF;padding:5px 12px;border-radius:999px;font-size:calc(0.78rem*var(--text-scale))!important;font-weight:700;box-shadow:0 3px 10px rgba(230,81,0,.3);white-space:nowrap;display:inline-block;}
    .stApp .badge-sim{background:linear-gradient(135deg,#F57F17,#FFA000);color:#FFFFFF;padding:4px 10px;border-radius:999px;font-size:calc(0.78rem*var(--text-scale))!important;font-weight:700;box-shadow:0 2px 8px rgba(245,127,23,.25);white-space:nowrap;display:inline-block;}
    .stApp .badge-feature{background:linear-gradient(135deg,#0277BD,#039BE5);color:#FFFFFF;padding:3px 10px;border-radius:999px;font-size:calc(0.75rem*var(--text-scale))!important;font-weight:600;margin-left:4px;box-shadow:0 2px 8px rgba(2,119,189,.22);white-space:nowrap;display:inline-block;}
    .history-card{background:#FFFFFF;border-radius:14px;padding:14px 16px;border-left:4px solid #039BE5;box-shadow:0 3px 12px rgba(2,119,189,.07);margin-bottom:10px;transition:all .2s ease;}
    .history-card:hover{transform:translateY(-2px);box-shadow:0 8px 20px rgba(2,119,189,.13);}
    .stApp .nav-cta{background:linear-gradient(135deg,#1B5E20 0%,#2E7D32 60%,#43A047 100%);color:#FFFFFF;text-align:center;padding:11px;border-radius:12px;font-weight:700;font-size:calc(0.95rem*var(--text-scale))!important;box-shadow:0 4px 14px rgba(27,94,32,.22);transition:all .2s ease;}
    a:hover .nav-cta{filter:brightness(1.1);transform:translateY(-2px);box-shadow:0 8px 22px rgba(27,94,32,.3);}
    .freq-display{text-align:center;padding:26px 20px;}
    .stApp .freq-value{font-size:calc(2.2rem*var(--text-scale))!important;font-weight:900;letter-spacing:.04em;background:linear-gradient(90deg,#1B5E20,#43A047);-webkit-background-clip:text;background-clip:text;-webkit-text-fill-color:transparent;}
    .stApp .freq-label{font-size:calc(0.85rem*var(--text-scale))!important;color:var(--ef-ink-soft);margin-top:6px;}
    [data-testid="stExpander"]{background:#FFFFFF;border:1px solid var(--ef-line)!important;border-radius:14px!important;box-shadow:0 3px 12px rgba(27,94,32,.05);overflow:hidden;}
    [data-testid="stExpander"] summary{font-weight:600;color:#1B5E20;}
    [data-testid="stExpander"] summary:hover{color:#2E7D32;}
    [data-testid="stAlert"]{border-radius:12px!important;box-shadow:0 3px 12px rgba(27,94,32,.06)!important;border:1px solid transparent!important;}
    .stTabs [data-baseweb="tab-list"]{gap:6px;background:#E9F4EB;padding:5px;border-radius:12px;}
    .stTabs [data-baseweb="tab"]{border-radius:9px;font-weight:600;color:#4E6B54;}
    .stTabs [aria-selected="true"]{background:#FFFFFF;color:#1B5E20;box-shadow:0 2px 8px rgba(27,94,32,.12);}
    div[data-testid="stDownloadButton"]>button{background:linear-gradient(135deg,#2E7D32,#43A047)!important;color:#FFFFFF!important;border:none!important;border-radius:12px!important;box-shadow:0 4px 14px rgba(46,125,50,.25)!important;font-weight:700!important;transition:all .2s ease!important;}
    div[data-testid="stDownloadButton"]>button:hover{transform:translateY(-2px)!important;box-shadow:0 8px 20px rgba(46,125,50,.35)!important;}
    div[role="radiogroup"] label{padding:8px 12px;border-radius:10px;transition:background .15s ease;border:1px solid transparent;}
    div[role="radiogroup"] label:hover{background:#F1F8E9;border-color:#DCEEDF;}
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
    if not KIMI_API_KEY:
        return False, (
            "尚未設定 Kimi API Key：請於 Streamlit Secrets 加入 KIMI_API_KEY"
            "（本地請在專案資料夾建立 .streamlit/secrets.toml；"
            "雲端請在 App 的 Settings → Secrets 面板設定）。"
            "設定完成後即可恢復 AI 識別功能，其他功能不受影響。"
        )
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


# ============================================================
# 📍 共享定位房間：即時地圖 iframe 產生器（Leaflet + Firebase）
# ============================================================
def build_share_map_html():
    """
    組出「共享定位房間」即時地圖的完整 HTML，交由 components.html 以 iframe 呈現。
    iframe 內自包含三個模組（位置資料與資料庫直連，不經過 Streamlit 伺服器）：
      ① 定位上報：watchPosition 節流（間隔 ≥5 秒且位移 ≥10 公尺才寫入資料庫）
      ② 即時顯示：onValue 監聽房間成員，即時更新 Leaflet marker（自己綠色、他人藍色，
         Popup 顯示名字與最後更新時間，lastSeen 超過 90 秒不顯示，fitBounds 自動取景，
         頂部徽章顯示線上人數）
      ③ 離場清理：onDisconnect().remove()，關閉頁面或斷網即自動從地圖移除
      ④ 容錯提示：任何環節（CDN、Firebase、瓦片、定位）失敗都會在地圖區顯示
         可見提示，不會靜默空白；瓦片連不上自動切換備用底圖，定位錯誤按
         PERMISSION_DENIED／POSITION_UNAVAILABLE／TIMEOUT 分別給出自查指引
    長輩模式：is_elder_mode 會同步放大 iframe 內字級。
    """
    elder = bool(st.session_state.is_elder_mode)
    top_font = "1.12rem" if elder else "0.95rem"
    base_font = "17px" if elder else "13px"
    pop_font = "15px" if elder else "12.5px"

    def _js(v):
        # 轉成安全的 JS 字串字面值（< > 一併轉義，避免惡意暱稱以 </script> 逃逸）
        return json.dumps(str(v), ensure_ascii=False).replace("<", "\\u003c").replace(">", "\\u003e")

    sl_map_doc = """
<!DOCTYPE html>
<html lang="zh-Hant">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>共享定位房間</title>
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<script src="https://www.gstatic.com/firebasejs/9.23.0/firebase-app-compat.js"></script>
<script src="https://www.gstatic.com/firebasejs/9.23.0/firebase-database-compat.js"></script>
<style>
html,body{margin:0;padding:0;height:100%;font-family:'Noto Sans TC','PingFang TC','Microsoft JhengHei',system-ui,sans-serif;background:#F2F8F3;font-size:__BASE_FONT__;}
#sl-top{display:flex;align-items:center;gap:10px;padding:11px 12px;background:linear-gradient(135deg,#1B5E20,#2E7D32);color:#FFFFFF;font-size:__TOP_FONT__;font-weight:500;box-sizing:border-box;}
#sl-top .code{background:rgba(255,255,255,.18);border:1px solid rgba(255,255,255,.35);border-radius:8px;padding:2px 10px;letter-spacing:4px;font-weight:800;}
#sl-gps{font-size:.92em;opacity:.95;}
#sl-badge{margin-left:auto;background:rgba(255,255,255,.18);border:1px solid rgba(255,255,255,.3);border-radius:999px;padding:3px 12px;white-space:nowrap;}
#map{height:calc(100% - 52px);border-radius:0 0 12px 12px;background:#E0E0E0;position:relative;overflow:hidden;}
.sl-map-note{position:absolute;top:10px;left:50%;transform:translateX(-50%);z-index:1100;background:rgba(255,255,255,.96);color:#1B5E20;border:1px solid #A5D6A7;border-radius:10px;padding:8px 14px;font-size:.95em;box-shadow:0 2px 8px rgba(0,0,0,.25);max-width:88%;text-align:center;line-height:1.5;}
.sl-pin{width:26px;height:26px;border-radius:50% 50% 50% 0;transform:rotate(-45deg);border:2px solid #FFFFFF;box-shadow:0 2px 8px rgba(0,0,0,.35);display:flex;align-items:center;justify-content:center;background:#1E88E5;}
.sl-pin.me{background:#43A047;}
.sl-pin span{transform:rotate(45deg);font-size:13px;line-height:1;}
.leaflet-popup-content{font-size:__POP_FONT__;}
</style>
</head>
<body>
<div id="sl-top">🏠 房間 <span class="code">__ROOM_HTML__</span><span id="sl-gps">📡 定位中…</span><span id="sl-badge">🟢 線上 0 人</span></div>
<div id="map"></div>
<script>
(function(){
"use strict";
var ROOM=__ROOM__,NAME=__NAME__,UID=__UID__,ROLE=__ROLE__;
var gpsEl=document.getElementById('sl-gps'),badgeEl=document.getElementById('sl-badge'),mapEl=document.getElementById('map');
function note(msg){var d=document.getElementById('sl-map-note');if(!d){d=document.createElement('div');d.id='sl-map-note';mapEl.appendChild(d);}d.textContent=msg;return d;}
function noteClear(){var d=document.getElementById('sl-map-note');if(d&&d.parentNode){d.parentNode.removeChild(d);}}
function failAll(msg){gpsEl.textContent='❌ '+msg;badgeEl.textContent='⚠️ 異常';note('❌ '+msg);}
try{
if(typeof L==='undefined'){failAll('地圖元件載入失敗：無法連線 unpkg.com 下載 Leaflet');return;}
if(typeof firebase==='undefined'){failAll('Firebase 元件載入失敗：無法連線 gstatic.com 下載 SDK');return;}
var db=null;
try{firebase.initializeApp({apiKey:__APIKEY__,databaseURL:__DBURL__});db=firebase.database();}
catch(e){failAll('Firebase 初始化失敗（配置可能有誤）：'+((e&&e.message)?String(e.message).slice(0,60):String(e)));return;}
var map=L.map('map',{zoomControl:true}).setView([22.1568,113.5615],13);
var tileOk=0,tileErr=0,tileStage=0;
var tiles=L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',{maxZoom:19,attribution:'&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> 貢獻者'});
tiles.on('tileload',function(){tileOk++;if(tileOk>=2){noteClear();}});
tiles.on('tileerror',function(){tileErr++;if(tileOk>0){return;}
  if(tileStage===0&&tileErr>=4){tileStage=1;tileErr=0;tiles.setUrl('https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}.png');note('⚠️ 主地圖底圖連不上，已自動切換備用底圖…');}
  else if(tileStage===1&&tileErr>=4){tileStage=2;note('⚠️ 地圖底圖載入失敗（圖源皆無法連線），但定位共享功能仍可運作');}
});
tiles.addTo(map);
note('🗺️ 地圖底圖載入中…');
var markers={},last={t:0,lat:null,lng:null},memberCount=-1;
var myRef=db.ref('rooms/'+ROOM+'/members/'+UID);
function esc(s){return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');}
function fmt(ts){if(!ts){return '—';}var d=new Date(ts);return d.toLocaleTimeString('zh-TW',{hour:'2-digit',minute:'2-digit',second:'2-digit'});}
function distM(la1,lo1,la2,lo2){var R=6371000,r=Math.PI/180;var dLa=(la2-la1)*r,dLo=(lo2-lo1)*r;var a=Math.sin(dLa/2)*Math.sin(dLa/2)+Math.cos(la1*r)*Math.cos(la2*r)*Math.sin(dLo/2)*Math.sin(dLo/2);return 2*R*Math.atan2(Math.sqrt(a),Math.sqrt(1-a));}
function pinIcon(isMe){var cls=isMe?'sl-pin me':'sl-pin';var emo=isMe?'😊':'🧑';return L.divIcon({className:'',iconSize:[26,26],iconAnchor:[13,26],popupAnchor:[0,-24],html:'<div class="'+cls+'"><span>'+emo+'</span></div>'});}
if(navigator.geolocation){
  var geoAnswered=false;
  var geoHint=setTimeout(function(){if(!geoAnswered){gpsEl.textContent='⏳ 尚未取得定位：請確認 Windows「設定 → 隱私權與安全性 → 位置」已開啟定位服務，且 Edge 地址列左側鎖／ⓘ 圖示已允許定位';}},12000);
  navigator.geolocation.watchPosition(function(pos){
    geoAnswered=true;clearTimeout(geoHint);
    var lat=pos.coords.latitude,lng=pos.coords.longitude,acc=pos.coords.accuracy,now=(new Date()).getTime();
    var moved=(last.lat===null)||distM(last.lat,last.lng,lat,lng)>=10;
    if((now-last.t)>=5000&&moved){
      last={t:now,lat:lat,lng:lng};
      myRef.set({name:NAME,lat:lat,lng:lng,acc:Math.round(acc),lastSeen:firebase.database.ServerValue.TIMESTAMP});
      gpsEl.textContent='✅ 定位共享中';
    }else{
      gpsEl.textContent='📡 定位中…（每 5 秒／10 公尺更新一次）';
    }
  },function(err){
    geoAnswered=true;clearTimeout(geoHint);
    var code=(err&&err.code)?err.code:0;
    if(code===1){gpsEl.textContent='❌ 定位被拒：請點 Edge 地址列左側鎖／ⓘ → 網站權限 → 位置 → 允許，再重新整理';}
    else if(code===2){gpsEl.textContent='❌ 取不到位置：請到 Windows「設定 → 隱私權與安全性 → 位置」開啟定位服務（桌上型電腦靠 Wi-Fi 推算定位）';}
    else if(code===3){gpsEl.textContent='⏳ 定位逾時，持續重試中…（桌上型電腦首次定位可能較慢）';}
    else{gpsEl.textContent='❌ 定位失敗，請檢查定位服務與瀏覽器權限';}
  },{enableHighAccuracy:true,maximumAge:2000,timeout:25000});
}else{
  gpsEl.textContent='❌ 此瀏覽器不支援定位';
}
myRef.onDisconnect().remove();
if(ROLE==='host'){db.ref('rooms/'+ROOM+'/meta').set({hostName:NAME,createdAt:firebase.database.ServerValue.TIMESTAMP});}
db.ref('rooms/'+ROOM+'/members').on('value',function(snap){
  var data=snap.val()||{};var seen={},pts=[],count=0,now=(new Date()).getTime();
  for(var uid in data){
    if(!Object.prototype.hasOwnProperty.call(data,uid)){continue;}
    var m=data[uid];
    if(!m||typeof m.lat!=='number'||typeof m.lng!=='number'){continue;}
    var age=(m.lastSeen)?(now-m.lastSeen):999999999;
    if(age>90000){continue;}
    count++;seen[uid]=1;pts.push([m.lat,m.lng]);
    var mk=markers[uid];
    if(!mk){mk=L.marker([m.lat,m.lng],{icon:pinIcon(uid===UID)}).addTo(map);mk.bindPopup('');markers[uid]=mk;}
    else{mk.setLatLng([m.lat,m.lng]);}
    var label=(uid===UID)?esc(NAME)+'（我）':esc(m.name||'成員');
    mk.setPopupContent('<b>'+label+'</b><br>🕒 最後更新：'+fmt(m.lastSeen));
  }
  for(var uid2 in markers){
    if(!Object.prototype.hasOwnProperty.call(markers,uid2)){continue;}
    if(!seen[uid2]){map.removeLayer(markers[uid2]);delete markers[uid2];}
  }
  badgeEl.textContent='🟢 線上 '+count+' 人';
  if(pts.length===1){map.setView(pts[0],16);}
  else if(pts.length>1&&count!==memberCount){map.fitBounds(L.latLngBounds(pts).pad(0.3));}
  memberCount=count;
},function(){
  badgeEl.textContent='⚠️ 連線失敗';gpsEl.textContent='❌ 無法連線 Firebase，請確認配置（databaseURL 是否完整）';
});
}catch(err){failAll('發生未預期錯誤：'+((err&&err.message)?String(err.message).slice(0,80):String(err)));}
})();
</script>
</body>
</html>
"""
    sl_map_doc = sl_map_doc.replace("__BASE_FONT__", base_font)
    sl_map_doc = sl_map_doc.replace("__TOP_FONT__", top_font)
    sl_map_doc = sl_map_doc.replace("__POP_FONT__", pop_font)
    sl_map_doc = sl_map_doc.replace("__ROOM_HTML__", html.escape(st.session_state.sl_room_code))
    sl_map_doc = sl_map_doc.replace("__ROOM__", _js(st.session_state.sl_room_code))
    sl_map_doc = sl_map_doc.replace("__NAME__", _js(st.session_state.sl_nickname))
    sl_map_doc = sl_map_doc.replace("__UID__", _js(st.session_state.sl_uid))
    sl_map_doc = sl_map_doc.replace("__ROLE__", _js(st.session_state.sl_role))
    sl_map_doc = sl_map_doc.replace("__APIKEY__", _js(FIREBASE_API_KEY))
    sl_map_doc = sl_map_doc.replace("__DBURL__", _js(FIREBASE_DATABASE_URL))
    return sl_map_doc

update_weather_and_aqi()


# ============================================================
# 頂部 Header
# ============================================================
audio_badge_text = "🟢 驅蟲運作" if st.session_state.audio_active else "🔴 驅蟲未啟"
col_head1, col_head2, col_head3 = st.columns([1.5, 0.9, 0.9])
with col_head1:
    st.markdown(
        '<div class="brand-wrap"><div class="brand-logo">🍀</div><div><div class="brand-title">絲野仙蹤 Eco-Family</div><div class="brand-sub">親子綠色呼吸智慧隨行助手</div></div></div>',
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
st.markdown('<div class="ef-divider"></div>', unsafe_allow_html=True)


# ============================================================
# 主選單
# ============================================================
if st.session_state.current_page == "menu":
    st.markdown(
        """
<div class="hero">
    <div class="hero-deco hero-deco-1">🦋</div>
    <div class="hero-deco hero-deco-2">🍄</div>
    <div class="hero-emoji">🍀</div>
    <div class="hero-title">絲野仙蹤</div>
    <div class="hero-title-en">Eco-Family</div>
    <div class="hero-sub">親子綠色呼吸智慧隨行助手</div>
    <div class="hero-chips">
        <span class="hero-chip">🗺️ 智慧路線</span>
        <span class="hero-chip">🎒 隨行裝備</span>
        <span class="hero-chip">🔍 動植物識別</span>
        <span class="hero-chip">🪰 驅蚊驅蟲</span>
        <span class="hero-chip">🚨 一鍵求救</span>
        <span class="hero-chip">📍 共享定位</span>
    </div>
</div>
""",
        unsafe_allow_html=True
    )
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
    if st.button("📍 共享定位房間", key="btn_m4", use_container_width=True):
        st.session_state.current_page = "share_location"
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
        bg_style = "border-left:6px solid #E65100;background:linear-gradient(135deg,#FFFDF2,#FFF6DC);" if is_best else ""
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
        <div class="nav-cta">🧭 開啟路線地圖導航</div>
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
        f'<div class="card freq-display"><div class="freq-value">{current_hz/1000:.1f} kHz</div><p class="freq-label">選擇頻率：<b>{freq_choice.split("-")[1].strip()}</b></p></div>',
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
<div style="text-align:center;padding:14px;background:linear-gradient(135deg,#F1F8E9,#E8F5E9);border-radius:14px;border:1px solid #DCEEDF;box-shadow:0 3px 10px rgba(27,94,32,.06);">
    <p style="font-size:0.95rem;color:#2E7D32;font-weight:bold;margin:0;letter-spacing:.02em;">__STATUS__</p>
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
<div style="text-align:center;padding:14px;background:linear-gradient(135deg,#FFEBEE,#FFDDE0);border-radius:14px;border:1px solid #FFCDD2;margin-bottom:14px;box-shadow:0 3px 12px rgba(198,40,40,.08);">
    <div id="sosGpsStatus" style="font-size:0.9rem;color:#C62828;font-weight:bold;margin-bottom:6px;">📡 正在感應當前衛星精確一鍵求救 GPS 座標...</div>
    <div id="regionNotice" style="font-size:0.85rem;color:#B71C1C;font-weight:bold;"></div>
</div>
<div style="background-color:#FFFFFF;border-radius:16px;padding:18px;border-left:5px solid #C62828;box-shadow:0 6px 20px rgba(198,40,40,.10);margin-bottom:16px;text-align:center;">
    <h4 style="color:#C62828;margin-top:0;font-size:1.05rem;">📋 一鍵複製精準 GPS 求救簡訊內容</h4>
    <div style="margin-bottom:12px;">
        <button id="copyBtn" onclick="copySosText()" style="width:100%;background:linear-gradient(135deg,#B71C1C,#E53935);color:white;font-size:1.1rem;font-weight:bold;padding:14px;border:none;border-radius:12px;cursor:pointer;box-shadow:0 4px 14px rgba(198,40,40,0.35);transition:all .2s ease;">📋 一鍵複製求救簡訊內容 (含實時經緯度)</button>
    </div>
    <p style="font-size:0.85rem;color:#666;text-align:left;margin-bottom:4px;font-weight:bold;">📱 將複製的內文貼至微信、簡訊發送給救援隊：</p>
    <textarea id="sosTextarea" readonly style="width:100%;height:140px;background-color:#FFFDFD;border-radius:10px;border:1px solid #FFCDD2;padding:10px;font-family:monospace;font-size:0.85rem;box-sizing:border-box;color:#333;"></textarea>
</div>
<style>
#copyBtn:hover{transform:translateY(-2px);box-shadow:0 8px 20px rgba(198,40,40,0.45);filter:brightness(1.05);}
#copyBtn:active{transform:translateY(0);}
.sos-tel{transition:all .2s ease;}
.sos-tel:hover{transform:translateY(-3px);filter:brightness(1.08);}
</style>
<div id="phoneArea" style="margin-bottom:16px;">
    <h5 style="margin-bottom:8px;color:#1B5E20;">📞 求助熱線直撥</h5>
    <div style="display:flex;gap:10px;">
        <a href="tel:999" class="sos-tel" style="flex:1;text-decoration:none;"><div style="background:linear-gradient(135deg,#01579B,#039BE5);color:white;text-align:center;padding:13px;border-radius:12px;font-weight:bold;box-shadow:0 3px 10px rgba(2,119,189,.28);">📞 999</div></a>
        <a href="tel:110" class="sos-tel" style="flex:1;text-decoration:none;"><div style="background:linear-gradient(135deg,#B71C1C,#E53935);color:white;text-align:center;padding:13px;border-radius:12px;font-weight:bold;box-shadow:0 3px 10px rgba(198,40,40,.28);">📞 110</div></a>
        <a href="tel:120" class="sos-tel" style="flex:1;text-decoration:none;"><div style="background:linear-gradient(135deg,#E65100,#FB8C00);color:white;text-align:center;padding:13px;border-radius:12px;font-weight:bold;box-shadow:0 3px 10px rgba(230,81,0,.28);">📞 120</div></a>
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
        <div class="card" style="border-left:5px solid #2E7D32; background:linear-gradient(135deg,#F1F8E9,#E8F5E9);">
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

# ============================================================
# 📍 共享定位房間（Leaflet 地圖 + Firebase Realtime Database）
# ============================================================
elif st.session_state.current_page == "share_location":
    st.markdown('<div class="back-btn">', unsafe_allow_html=True)
    if st.button("← 返回主頁面", key="back_share"):
        st.session_state.current_page = "menu"
        st.session_state.sl_room_code = ""
        st.session_state.sl_uid = ""
        st.session_state.sl_role = ""
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown(
        '<div class="card"><h3 style="margin-top:0px;color:#1B5E20;">📍 共享定位房間</h3>'
        '<p style="font-size:0.9rem;color:#2E7D32;margin-bottom:0;">建立或加入房間後，地圖上可<b>即時看見房間內每位成員的名字與位置</b>，'
        '適合親子出遊時互相確認彼此位置。</p></div>',
        unsafe_allow_html=True
    )
    st.markdown(
        '<div class="card" style="border-left:5px solid #00695C;background:linear-gradient(135deg,#E0F2F1,#E8F5E9);">'
        '<p style="font-size:0.82rem;color:#00695C;margin:0;"><b>🔐 定位授權說明：</b>你的即時位置<b>只會</b>對房間內成員可見；'
        '離開此頁面或關閉瀏覽器即自動停止共享並移除你的標記（系統不保存任何歷史軌跡）。'
        '首次使用時瀏覽器會詢問定位授權，請點選「允許」。</p></div>',
        unsafe_allow_html=True
    )

    if not FIREBASE_CONFIGURED:
        st.markdown(
            '<div class="card" style="border-left:5px solid #E65100;background:linear-gradient(135deg,#FFF3E0,#FFECB3);">'
            '<h4 style="margin-top:0;color:#BF360C;">🛠️ 尚未設定 Firebase 配置</h4>'
            '<p style="font-size:0.85rem;color:#BF360C;margin-bottom:6px;">共享定位需要一個免費的 Firebase Realtime Database '
            '（用 Google 帳號即可建立，約 10 分鐘）。請依照隨本程式交付的<b>《共享定位房間部署指南.md》</b>操作：</p>'
            '<p style="font-size:0.85rem;color:#BF360C;margin:0;">① 到 <b>console.firebase.google.com</b> 建立專案（Spark 免費方案）→ '
            '② 建立 Realtime Database 並貼上安全規則 → ③ 把程式碼最上方的 <b>FIREBASE_API_KEY</b> 與 '
            '<b>FIREBASE_DATABASE_URL</b> 換成你自己的配置。完成後本頁即可正常使用。</p></div>',
            unsafe_allow_html=True
        )

    in_room = bool(st.session_state.sl_room_code and st.session_state.sl_uid)
    pending_join = bool(st.session_state.sl_room_code and not st.session_state.sl_uid)

    if in_room:
        role_text = "房主" if st.session_state.sl_role == "host" else "成員"
        try:
            _host = st.context.headers.get("host", "")
        except Exception:
            _host = ""
        if _host:
            _proto = "http" if (_host.startswith("localhost") or _host.startswith("127.0.0.1")) else "https"
            sl_invite_url = f"{_proto}://{_host}/?page=share_location&room={st.session_state.sl_room_code}"
        else:
            sl_invite_url = "你的網址/?page=share_location&room=" + st.session_state.sl_room_code
        st.markdown(f"""
<div class="card" style="border-left:5px solid #2E7D32;background:linear-gradient(135deg,#F1F8E9,#E8F5E9);">
    <div style="font-size:0.85rem;color:#1B5E20;font-weight:bold;">🏠 你的房間號（把這 4 碼告訴家人即可加入）</div>
    <div style="font-size:2.2rem;letter-spacing:10px;font-weight:900;color:#1B5E20;margin:4px 0;">{html.escape(st.session_state.sl_room_code)}</div>
    <div style="font-size:0.82rem;color:#5B6B60;margin-bottom:8px;">你的身分：{role_text}｜顯示名字：{html.escape(st.session_state.sl_nickname)}</div>
    <div style="font-size:0.8rem;color:#00695C;background:#FFFFFF;border:1px dashed #A5D6A7;border-radius:8px;padding:8px;word-break:break-all;">🔗 邀請連結（家人點開後自動帶入本房間，免手動輸入房間號）：<br><b>{html.escape(sl_invite_url)}</b></div>
</div>
""", unsafe_allow_html=True)
        if st.button("🚪 離開房間", key="sl_btn_leave", use_container_width=True):
            st.session_state.sl_room_code = ""
            st.session_state.sl_uid = ""
            st.session_state.sl_role = ""
            st.rerun()
        if FIREBASE_CONFIGURED:
            st.markdown(
                '<div class="card" style="padding:10px 14px;"><p style="font-size:0.82rem;color:#2E7D32;margin:0;">🗺️ 即時地圖：綠色 😊 是你自己，藍色 🧑 是其他成員。點擊人像可看名字與最後更新時間。</p></div>',
                unsafe_allow_html=True
            )
            components.html(build_share_map_html(), height=520)
        else:
            st.info("房間已建立 ✅ 完成《共享定位房間部署指南.md》中的 Firebase 設定後，這裡就會顯示即時地圖。")
    elif pending_join:
        st.markdown(
            '<div class="card" style="border-left:5px solid #00695C;background:linear-gradient(135deg,#E0F2F1,#E8F5E9);">'
            '<h4 style="margin-top:0;color:#00695C;">🎉 你收到房間邀請！</h4>'
            '<p style="font-size:0.88rem;color:#00695C;margin-bottom:0;">房間號 <b style="font-size:1.4rem;letter-spacing:6px;">'
            + html.escape(st.session_state.sl_room_code) + '</b>｜輸入你的名字後即可加入，地圖上即時看見房內所有人。</p></div>',
            unsafe_allow_html=True
        )
        nickname = st.text_input("你在房間內顯示的名字", value=st.session_state.sl_nickname, key="sl_nick_input", placeholder="例如：森森媽媽")
        if st.button("🚪 加入房間", key="sl_btn_join_link", use_container_width=True):
            if not nickname.strip():
                st.warning("請先輸入你的名字再加入房間。")
            else:
                st.session_state.sl_nickname = nickname.strip()
                st.session_state.sl_uid = uuid.uuid4().hex[:12]
                st.session_state.sl_role = "guest"
                st.rerun()
    else:
        st.markdown("##### 👤 第一步：設定你的名字")
        nickname = st.text_input("你在房間內顯示的名字", value=st.session_state.sl_nickname, key="sl_nick_input", placeholder="例如：森森媽媽")
        join_code = st.text_input("🔑 想加入的房間號（4 位英數字，沒有可留空）", key="sl_join_input", placeholder="例如：7KQF").strip().upper()
        c_create, c_join = st.columns(2)
        with c_create:
            if st.button("➕ 建立新房間", key="sl_btn_create", use_container_width=True):
                if not nickname.strip():
                    st.warning("請先輸入你的名字再建立房間。")
                else:
                    st.session_state.sl_nickname = nickname.strip()
                    st.session_state.sl_room_code = "".join(secrets.choice(SL_CODE_ALPHABET) for _ in range(4))
                    st.session_state.sl_uid = uuid.uuid4().hex[:12]
                    st.session_state.sl_role = "host"
                    st.rerun()
        with c_join:
            if st.button("🚪 加入房間", key="sl_btn_join", use_container_width=True):
                code = join_code.strip().upper()
                if not nickname.strip():
                    st.warning("請先輸入你的名字再加入房間。")
                elif len(code) != 4 or any(ch not in SL_CODE_ALPHABET for ch in code):
                    st.warning("房間號須為 4 位英數字（不含 0、1、I、O），請向房主確認。")
                else:
                    st.session_state.sl_nickname = nickname.strip()
                    st.session_state.sl_room_code = code
                    st.session_state.sl_uid = uuid.uuid4().hex[:12]
                    st.session_state.sl_role = "guest"
                    st.rerun()
        st.caption("💡 房間號由系統隨機生成 4 位英數字（已剔除易混淆的 0、1、I、O），方便當面口頭轉述；也可直接把房間內顯示的邀請連結傳給家人。")

    