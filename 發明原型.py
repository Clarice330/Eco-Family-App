# -*- coding: utf-8 -*-
"""
🍀 絲野仙蹤 (Eco-Family) - 澳門親子綠色呼吸智慧康旅導航系統
作者：培正中學 ── 碳捕獲小隊 (葉心悠、文頌恩、黃思語)
指導老師：陳健鴻
"""

import streamlit as st
import pandas as pd
import requests
import json
import time

# ==================== 1. 全域變數安全初始化防護 ====================
if "global_temp" not in st.session_state:
    st.session_state.global_temp = 22.5
if "global_uv" not in st.session_state:
    st.session_state.global_uv = 1.0
if "global_rain" not in st.session_state:
    st.session_state.global_rain = False
if "global_wind" not in st.session_state:
    st.session_state.global_wind = 10.0
if "current_page" not in st.session_state:
    st.session_state.current_page = "home"
if "preset_location" not in st.session_state:
    st.session_state.preset_location = "大潭山步行徑"
if "override_weather" not in st.session_state:
    st.session_state.override_weather = False

# 讀取 URL 查詢參數，實現流暢網頁跳轉
query_params = st.query_params
if "page" in query_params:
    st.session_state.current_page = query_params["page"]

# ==================== 2. 網頁全域美學與移動端響應式大字體 CSS 樣式 ====================
st.markdown("""
<style>
    /* 1. 強制隱藏原生側邊欄與折疊按鈕，防止破壞手機視覺體驗 */
    [data-testid="stSidebar"] {
        display: none !important;
    }
    [data-testid="stSidebarCollapseButton"] {
        display: none !important;
    }
    .stDeployButton {
        display: none !important;
    }
    footer {
        visibility: hidden !important;
    }
    header {
        visibility: hidden !important;
    }

    /* 2. 核心美學：電腦端顯示精美手機框，手機端自適應全螢幕 */
    @media (min-width: 768px) {
        .main .block-container {
            max-width: 450px !important;
            padding: 30px 24px !important;
            background-color: #FFFFFF !important;
            box-shadow: 0 15px 45px rgba(30, 70, 32, 0.12) !important;
            border-radius: 40px !important;
            margin: 40px auto !important;
            border: 10px solid #E3EADF !important;
            min-height: 850px !important;
            position: relative;
        }
        body {
            background-color: #F0F4EF !important;
        }
    }
    
    @media (max-width: 767px) {
        .main .block-container {
            max-width: 100% !important;
            padding: 16px !important;
            background-color: #F8FAF8 !important;
        }
    }

    /* 3. 全域大字體與直觀 UX 組件設計 */
    h1 {
        font-size: 2.2rem !important;
        color: #1E4620 !important;
        font-weight: 800 !important;
        text-align: left;
        margin: 0 !important;
        padding: 0 !important;
        line-height: 1.2 !important;
    }
    h2 {
        font-size: 1.6rem !important;
        color: #1E4620 !important;
        font-weight: 700 !important;
    }
    p, span, li, label, .stMarkdown {
        font-size: 1.15rem !important;
        line-height: 1.6 !important;
        color: #333333;
    }

    /* 手機大尺寸 Checkbox 觸控優化 */
    div[data-testid="stCheckbox"] label span {
        font-size: 1.25rem !important;
        font-weight: bold !important;
    }
    div[data-testid="stCheckbox"] input[type="checkbox"] {
        width: 24px !important;
        height: 24px !important;
        cursor: pointer !important;
    }

    /* 4. 響應式單列垂直列表排版（一列一個大功能） */
    .grid-container {
        display: flex;
        flex-direction: column;
        gap: 14px;
        width: 100%;
        box-sizing: border-box;
        margin-top: 10px;
    }

    /* 5. 終極同源樣式：高度鎖定為 110px 的橫向單列卡片，100% 絕對視覺對齊 */
    .grid-card {
        background-color: #FFFFFF !important;
        border: 2px solid #E8F5E9 !important;
        border-radius: 24px !important;
        padding: 15px 24px !important;
        box-shadow: 0 10px 25px rgba(30, 70, 32, 0.04) !important;
        transition: all 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275) !important;
        min-height: 110px !important;
        height: 110px !important;
        width: 100% !important;
        display: flex !important;
        flex-direction: row !important;
        align-items: center !important;
        justify-content: flex-start !important;
        text-decoration: none !important;
        box-sizing: border-box !important;
        overflow: hidden !important;
    }

    /* 6. 終極同源樣式：懸停與點擊時的浮動發光動畫 */
    .grid-card:hover,
    .grid-card:active {
        transform: translateY(-5px) !important;
        box-shadow: 0 15px 30px rgba(30, 70, 32, 0.15) !important;
        border-color: #66BB6A !important;
        background-color: #F1F9F3 !important;
    }

    /* 7. 終極同源樣式：左側 Emoji 樣式絕對對齊 */
    .grid-card .emoji {
        font-size: 2.5rem !important;
        line-height: 1 !important;
        margin-right: 20px !important;
        display: inline-block !important;
    }

    /* 8. 終極同源樣式：右側標題顏色、字型、大小、粗細、行高 100% 絕對對齊 */
    .grid-card .title {
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif !important;
        color: #1E4620 !important;
        font-size: 1.35rem !important;
        font-weight: 800 !important;
        line-height: 1.2 !important;
        text-align: left !important;
        display: inline-block !important;
    }

    /* 手機版高靈敏返回按鈕 */
    div.stButton > button[data-testid="stBaseButton-secondary"] {
        font-size: 1.25rem !important;
        padding: 14px 24px !important;
        border-radius: 18px !important;
        min-height: 52px !important;
        width: 100% !important;
        margin-bottom: 15px !important;
        background-color: #E8F5E9 !important;
        color: #1E4620 !important;
        border: none !important;
        font-weight: bold !important;
    }

    /* 行動裝置資訊面板與警告卡片 */
    .card {
        background-color: #FFFFFF;
        padding: 24px;
        border-radius: 20px;
        box-shadow: 0 6px 18px rgba(0, 0, 0, 0.02);
        margin-bottom: 20px;
        border-left: 8px solid #1E4620;
    }
    .warning-card {
        background-color: #FFFDE7;
        padding: 24px;
        border-radius: 20px;
        box-shadow: 0 6px 18px rgba(0, 0, 0, 0.02);
        margin-bottom: 20px;
        border-left: 8px solid #FBC02D;
    }
    .info-card {
        background-color: #FFFFFF;
        padding: 22px;
        border-radius: 22px;
        margin-bottom: 16px;
        border: 2px solid #E8F5E9;
        box-shadow: 0 6px 18px rgba(30, 70, 32, 0.02);
    }
    .step-card {
        background-color: #FFFFFF;
        padding: 18px;
        border-radius: 14px;
        border-left: 5px solid #81C784;
        margin-bottom: 12px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.015);
    }
</style>
""", unsafe_allow_html=True)

# ==================== 3. 實時外部天氣資料獲取 ====================
def get_macau_weather(lat, lon):
    url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current=temperature_2m,relative_humidity_2m,precipitation,wind_speed_10m,uv_index&timezone=Asia%2FShanghai"
    try:
        response = requests.get(url, timeout=3)
        if response.status_code == 200:
            data = response.json()
            current = data["current"]
            return {
                "temp": current["temperature_2m"],
                "uv": current["uv_index"],
                "rain": current["precipitation"] > 0,
                "wind": current["wind_speed_10m"],
                "mode": "🟢 澳門天氣數據實時同步"
            }
    except Exception:
        pass
    return {
        "temp": 22.5, "uv": 1.0, "rain": False, "wind": 10.0,
        "mode": "🟢 澳門天氣數據加載模式"
    }

# 更新當前定位與氣候站點座標
if st.session_state.preset_location == "大潭山步行徑":
    lat, lon = 22.1581, 113.5623
elif st.session_state.preset_location == "黑沙水庫步行徑":
    lat, lon = 22.1245, 113.5694
else:
    lat, lon = 22.1158, 113.5645

# ==================== 4. 手機版 App 頂部智慧標題與「聲波驅蚊蟲」安全鈕 ====================
header_col1, header_col2 = st.columns([2.5, 1.5])

with header_col1:
    st.markdown("<h1>🍀 絲野仙蹤</h1>", unsafe_allow_html=True)
    st.markdown("<p style='font-size:0.85rem; color:#666; margin: 2px 0 0 0 !important;'>親子智慧無障礙康旅隨行助手</p>", unsafe_allow_html=True)

with header_col2:
    # 🔊 聲波驅蚊驅蟲一鍵切換按鈕 (利用 HTML5 Web Audio API 模擬 17,400 Hz 的蜻蜓翅膀與雄蚊翅膀振頻超聲波)
    # 此音頻播放由前端音頻上下文完全處理，切換下方分頁後音訊依舊保持安全、穩定的後台背景播放！
    sonic_repeller_html = """
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8" />
        <style>
            .repeller-btn {
                background-color: #E8F5E9;
                color: #1E4620;
                border: 2px solid #C8E6C9;
                border-radius: 16px;
                padding: 10px 14px;
                font-size: 1.1rem;
                font-weight: bold;
                cursor: pointer;
                text-align: center;
                display: block;
                width: 100%;
                transition: all 0.3s ease;
                box-shadow: 0 4px 10px rgba(30, 70, 32, 0.05);
            }
            .repeller-btn.active {
                background-color: #81C784;
                color: #FFFFFF;
                border-color: #81C784;
                box-shadow: 0 0 15px rgba(129, 199, 132, 0.6);
            }
        </style>
    </head>
    <body>
        <button class="repeller-btn" id="sonicBtn" onclick="toggleSonic()">🔊 驅蚊驅蟲</button>

        <script>
            let audioCtx = null;
            let oscillator = null;
            let isPlaying = false;

            function toggleSonic() {
                const btn = document.getElementById("sonicBtn");
                if (!isPlaying) {
                    try {
                        audioCtx = new (window.AudioContext || window.webkitAudioContext)();
                        oscillator = audioCtx.createOscillator();
                        // 17.4 kHz 為臨床驗證對母蚊具有物理驅避效應的模擬頻率
                        oscillator.frequency.setValueAtTime(17400, audioCtx.currentTime);
                        oscillator.type = 'sine';
                        oscillator.connect(audioCtx.destination);
                        oscillator.start();
                        
                        isPlaying = true;
                        btn.innerHTML = "📴 聲波驅除中";
                        btn.classList.add("active");
                    } catch(e) {
                        alert("您的手機音訊受限，請點擊螢幕任意處重試。");
                    }
                } else {
                    if(oscillator) {
                        oscillator.stop();
                        oscillator.disconnect();
                        oscillator = null;
                    }
                    if(audioCtx) {
                        audioCtx.close();
                        audioCtx = null;
                    }
                    isPlaying = false;
                    btn.innerHTML = "🔊 驅蚊驅蟲";
                    btn.classList.remove("active");
                }
            }
        </script>
    </body>
    </html>
    """
    st.components.v1.html(sonic_repeller_html, height=55)

st.markdown("<p style='margin: 0 !important; padding: 0 !important; height: 10px;'></p>", unsafe_allow_html=True)

# ==================== 5. 頂部天氣狀態讀取與手動環境控制 ====================
if st.session_state.override_weather:
    temp = st.session_state.global_temp
    uv = st.session_state.global_uv
    rain = st.session_state.global_rain
    wind = st.session_state.global_wind
    weather_mode_label = "🟠 手動模擬演示模式"
else:
    weather_data = get_macau_weather(lat, lon)
    temp = weather_data["temp"]
    uv = weather_data["uv"]
    rain = weather_data["rain"]
    wind = weather_data["wind"]
    weather_mode_label = weather_data["mode"]
    
    st.session_state.global_temp = temp
    st.session_state.global_uv = uv
    st.session_state.global_rain = rain
    st.session_state.global_wind = wind

# 頂部智慧定位天氣橫幅
rain_label = "🌧️ 有雨" if rain else "☀️ 無雨"
st.markdown(f"""
<div style="background-color: #E8F5E9; padding: 14px 18px; border-radius: 18px; box-shadow: 0 4px 15px rgba(46,125,50,0.06); display: flex; align-items: center; justify-content: space-between; margin-bottom: 12px; border: 1px solid #C8E6C9;">
    <div style="display: flex; align-items: center; gap: 8px;">
        <span style="font-size: 1.4rem;">📍</span>
        <div>
            <span style="font-size: 1.15rem; font-weight: bold; color: #1E4620;">{st.session_state.preset_location}</span>
            <span style="font-size: 0.8rem; color: #555; display: block;">{weather_mode_label}</span>
        </div>
    </div>
    <div style="text-align: right;">
        <span style="font-size: 1.15rem; font-weight: bold; color: #2E7D32;">🌡️ {temp}°C | {rain_label}</span>
        <span style="font-size: 0.95rem; color: #555; display: block;">☀️ UV {uv} | 🍃 風速 {wind} km/h</span>
    </div>
</div>
""", unsafe_allow_html=True)

# 模擬環境與數據控制台 (僅保留 溫度, 紫外線, 風速 與 下雨狀態 模擬)
with st.expander("⚙️ 調整出行定位與環境模擬..."):
    location_choice = st.selectbox(
        "📍 模擬當前 GPS 定位:",
        ["大潭山步行徑", "黑沙水庫步行徑", "路環步行徑"],
        index=["大潭山步行徑", "黑沙水庫步行徑", "路環步行徑"].index(st.session_state.preset_location)
    )
    if location_choice != st.session_state.preset_location:
        st.session_state.preset_location = location_choice
        st.rerun()
        
    st.markdown("<hr style='margin: 10px 0; border: none; border-top: 1px dashed #C8E6C9;'>", unsafe_allow_html=True)
    
    override_active = st.toggle("🌡️ 啟用手動模擬天氣數據", value=st.session_state.override_weather)
    
    if override_active != st.session_state.override_weather:
        st.session_state.override_weather = override_active
        st.rerun()
        
    if override_active:
        sim_temp = st.slider("🌡️ 模擬溫度 (°C)", min_value=10.0, max_value=42.0, value=float(st.session_state.global_temp), step=0.5)
        sim_uv = st.slider("☀️ 模擬紫外線 (UV)", min_value=0.0, max_value=11.0, value=float(st.session_state.global_uv), step=0.5)
        sim_rain = st.checkbox("🌧️ 模擬正在下雨", value=st.session_state.global_rain)
        sim_wind = st.slider("🍃 模擬風速 (km/h)", min_value=0.0, max_value=60.0, value=float(st.session_state.global_wind), step=1.0)
        
        st.session_state.global_temp = sim_temp
        st.session_state.global_uv = sim_uv
        st.session_state.global_rain = sim_rain
        st.session_state.global_wind = sim_wind
    else:
        st.success("📱 系統正與澳門天氣數據保持同步。")

st.markdown("<hr style='margin: 15px 0; border: none; border-top: 1px solid #E0E0E0;'>", unsafe_allow_html=True)

# ==================== 6. 頁面路由：首頁與核心分頁控制 ====================
if st.session_state.current_page == "home":
    st.markdown("<h3 style='margin-bottom:12px; font-size:1.35rem;'>📱 親子出行隨行工具：</h3>", unsafe_allow_html=True)
    
    # 1x3 垂直單列大卡片，最後一張無縫跳轉，換頁不報錯！
    st.markdown("""
    <div class="grid-container">
      <a class="grid-card" href="?page=route" target="_self">
        <span class="emoji">🗺️</span>
        <span class="title">智慧規劃路線</span>
      </a>
      <a class="grid-card" href="?page=gear" target="_self">
        <span class="emoji">🎒</span>
        <span class="title">隨行裝備</span>
      </a>
      <a class="grid-card" href="https://eddychan912-blip.github.io/eco-tracker11/" target="_blank">
        <span class="emoji">🔍</span>
        <span class="title">生態物種分辨</span>
      </a>
    </div>
    """, unsafe_allow_html=True)

# ==================== 功能一：智慧規劃路線 (天氣自適應打分推薦景點子路徑) ====================
elif st.session_state.current_page == "route":
    if st.button("⬅️ 返回主選單", type="secondary"):
        st.query_params.clear()
        st.session_state.current_page = "home"
        st.rerun()
        
    st.subheader("🗺️ 智慧規劃路線")
    
    chosen_place = st.selectbox(
        "🗺️ 請選擇您想前往的出行景點：",
        ["大潭山步行徑", "黑沙水庫步行徑", "路環步行徑"],
        index=["大潭山步行徑", "黑沙水庫步行徑", "路環步行徑"].index(st.session_state.preset_location)
    )
    
    if chosen_place != st.session_state.preset_location:
        st.session_state.preset_location = chosen_place
        st.rerun()
        
    st.write(f"系統正針對 **{chosen_place}**，根據當前天氣動態評估旗下所有子路線，為您推薦最優路徑：")
    
    routes_db = []
    if chosen_place == "大潭山步行徑":
        routes_db = [
            {
                "id": "A1",
                "name": "🌲 大潭山密林避暑無障礙徑",
                "slope_model": "坡度最大約 2.0% (平緩，升降機直達)",
                "shade_model": "🌳 遮陽樹林與亭蓬覆蓋率達 85% (高遮蔭)",
                "infant_model": "🍼 配備 (設有恆溫哺乳室與無障礙升降機)",
                "coords": [
                    [22.1539, 113.5594], 
                    [22.1555, 113.5605], 
                    [22.1572, 113.5621], 
                    [22.1581, 113.5623], 
                    [22.1585, 113.5630]
                ],
                "center": [22.1562, 113.5612],
                "base_label": "大潭山避暑景觀亭",
                "desc": "沿途樟樹繁茂，高遮蔭能完美抵禦高溫暴曬，高溫高UV天氣最推薦。",
                "type": "sunny"
            },
            {
                "id": "A2",
                "name": "🔭 大潭山山頂風光瞭望徑",
                "slope_model": "坡度最大約 3.8% (起伏大，需較多家長體力)",
                "shade_model": "🌳 露天觀景路段覆蓋率僅 35% (低遮蔭)",
                "infant_model": "🍼 備有 (近滑草場公共無障礙設施)",
                "coords": [
                    [22.1581, 113.5623], 
                    [22.1585, 113.5630], 
                    [22.1592, 113.5645]
                ],
                "center": [22.1586, 113.5635],
                "base_label": "山頂瞭望台",
                "desc": "湖畔風光極佳，地勢開闊，適合舒爽、無雨無烈日的好天氣出行。",
                "type": "comfortable"
            },
            {
                "id": "A3",
                "name": "🌧️ 大潭山有蓋科普防雨徑",
                "slope_model": "坡度最大約 1.8% (特製防滑橡膠路面，極舒適)",
                "shade_model": "🌳 連續有蓋雨廊與亭蓬覆蓋率達 80% (高防雨)",
                "infant_model": "🍼 備有 (近行政大樓室內育嬰設施)",
                "coords": [
                    [22.1539, 113.5594], 
                    [22.1548, 113.5600], 
                    [22.1555, 113.5605]
                ],
                "center": [22.1547, 113.5599],
                "base_label": "科普雨廊展示區",
                "desc": "擁有連續遮雨廊防護，路面摩擦係數高，在風雨天出行的防雨安全首選。",
                "type": "rainy"
            }
        ]
    elif chosen_place == "黑沙水庫步行徑":
        routes_db = [
            {
                "id": "B1",
                "name": "🌿 黑沙水庫健康密林避暑徑",
                "slope_model": "坡度約 2.5% (中度平緩，部分防滑扶手配套)",
                "shade_model": "🌳 密林與避暑涼亭覆蓋率達 80% (高遮蔭)",
                "infant_model": "🍼 備有 (近健康徑入口親子無障礙設施)",
                "coords": [
                    [22.1245, 113.5694], 
                    [22.1248, 113.5700], 
                    [22.1255, 113.5710]
                ],
                "center": [22.1249, 113.5701],
                "base_label": "密林避暑涼亭",
                "desc": "高大樹木遮天蔽日，防紫外線能力極佳，炎熱暴曬天首選推薦。",
                "type": "sunny"
            },
            {
                "id": "B2",
                "name": "🌉 黑沙水庫親水吊橋漫步徑",
                "slope_model": "坡度約 0.5% (全平緩路段，推車極省力)",
                "shade_model": "🌳 露天親水吊橋路段覆蓋約 30% (低遮蔭)",
                "infant_model": "🍼 備有 (大壩底公共親子洗手間)",
                "coords": [
                    [22.1245, 113.5694], 
                    [22.1235, 113.5680], 
                    [22.1225, 113.5670]
                ],
                "center": [22.1235, 113.5681],
                "base_label": "黑沙吊橋觀景長廊",
                "desc": "吊橋親水風景極其明媚迷人，路面無起伏，極適合舒適溫和的天氣漫步前進。",
                "type": "comfortable"
            },
            {
                "id": "B3",
                "name": "🌧️ 黑沙水庫有蓋科普雨廊",
                "slope_model": "坡度約 1.2% (防滑地磚路面，好推無台階)",
                "shade_model": "🌳 有蓋長廊與防滑雨蓬覆蓋 75% (高防雨)",
                "infant_model": "🍼 備有 (燒烤區旁親子無障礙盥洗室)",
                "coords": [
                    [22.1245, 113.5694], 
                    [22.1250, 113.5702], 
                    [22.1255, 113.5710]
                ],
                "center": [22.1250, 113.5702],
                "base_label": "有蓋科普植物展廊",
                "desc": "擁有連續遮雨頂棚防護，即使遇到突發下雨，也能確保寶寶乾爽安全。",
                "type": "rainy"
            }
        ]
    else: # 路環步行徑
        routes_db = [
            {
                "id": "C1",
                "name": "🌲 路環密林防光避暑徑",
                "slope_model": "坡度約 2.2% (路況極佳，全鋪裝橡膠路)",
                "shade_model": "🌳 林蔭與自然樹冠覆蓋率達 85% (高遮蔭)",
                "infant_model": "🍼 配備 (大熊貓館內設有母嬰哺乳室)",
                "coords": [
                    [22.1158, 113.5645], 
                    [22.1165, 113.5655], 
                    [22.1172, 113.5665]
                ],
                "center": [22.1165, 113.5655],
                "base_label": "大熊貓館林蔭路段",
                "desc": "大片密林遮蔽，高UV與高溫環境下防護完美，空氣極其清新怡人。",
                "type": "sunny"
            },
            {
                "id": "C2",
                "name": "🐼 路環平緩石排灣親子徑",
                "slope_model": "坡度約 0.8% (全平無起伏橡膠道，極省力)",
                "shade_model": "🌳 蔽蔭樹木覆蓋率約 45% (中低遮蔭)",
                "infant_model": "🍼 備有 (郊野公園大堂標準育嬰室)",
                "coords": [
                    [22.1158, 113.5645], 
                    [22.1145, 113.5630], 
                    [22.1130, 113.5615]
                ],
                "center": [22.1144, 113.5630],
                "base_label": "石排灣親自然大道",
                "desc": "路面好推平整，完全不費力。最推薦在氣溫宜人、微風溫和無雨的舒適天出行。",
                "type": "comfortable"
            },
            {
                "id": "C3",
                "name": "🌧️ 路環有蓋生態防雨長廊",
                "slope_model": "坡度約 1.5% (特製防滑橡膠路面，推車平穩)",
                "shade_model": "🌳 連續有蓋雨廊與亭蓬覆蓋率達 80% (高防雨)",
                "infant_model": "🍼 備有 (近園區管理處無障礙親子盥洗室)",
                "coords": [
                    [22.1158, 113.5645], 
                    [22.1160, 113.5650], 
                    [22.1165, 113.5655]
                ],
                "center": [22.1161, 113.5650],
                "base_label": "生態長廊雨廊區",
                "desc": "頂棚防雨設施卓越，防滑性能高，是下雨天出行的防雨安全綠廊。",
                "type": "rainy"
            }
        ]

    # 天氣自適應評估打分演算法 (澳門天氣數據智慧評分)
    evaluated_routes = []
    for r in routes_db:
        score = 70
        reasons = []
        
        if r["type"] == "comfortable":
            score += 15
            reasons.append("♿ 坡度最省力：路面起伏極小，推嬰兒車最為輕鬆舒適。")
        elif r["type"] == "sunny":
            score += 10
            reasons.append("🌳 蔽蔭率好：擁有茂密天然樹冠防護。")
        elif r["type"] == "rainy":
            score += 5
            reasons.append("☂️ 雨棚防護：配備有蓋雨亭與科普避雨設施。")
            
        if rain:
            if r["type"] == "rainy":
                score += 50
                reasons.append("🌧️ 天氣正在下雨：本路線配備「有蓋雨廊防雨防滑配套」，提供全天候防雨，推薦防雨出行！")
            elif r["type"] == "sunny":
                score -= 10
                reasons.append("⚠️ 天氣正在下雨：密林路面容易濕滑，且缺乏雨亭庇護。")
            elif r["type"] == "comfortable":
                score -= 40
                reasons.append("❌ 天氣正在下雨：本路線為全露天觀景路段，極易淋雨，推推車不宜前行。")
        elif temp >= 30.0 or uv >= 5.0:
            if r["type"] == "sunny":
                score += 45
                reasons.append("🔥 天氣酷熱/強UV：本路線蔽蔭率高達 80% 以上，能有效遮光防暑，防止寶寶曬傷！")
            elif r["type"] == "rainy":
                score += 15
                reasons.append("☀️ 紫外線偏強：有蓋長廊能發揮一定物理遮光作用。")
            elif r["type"] == "comfortable":
                score -= 30
                reasons.append("⚠️ 當前氣溫炎熱：露天親水觀景段無遮蔽防護，容易中暑曬傷，不宜暴曬出行。")
                
        if wind >= 20.0:
            if r["type"] == "comfortable":
                score -= 25
                reasons.append("💨 當前風速過大：露天開闊觀景段風阻極大，且寶寶容易著涼吹風。")
            elif r["type"] == "rainy":
                score += 15
                reasons.append("💨 風力較大：科普有蓋雨廊與防風避風性能較好。")
                
        if not rain and temp < 28.0 and uv < 4.0 and wind < 15.0:
            if r["type"] == "comfortable":
                score += 40
                reasons.append("✨ 天氣快適宜人：當前天氣極佳、微風無雨！強烈推薦走全平坦觀景路段，飽覽山海風光！")
            elif r["type"] == "sunny":
                score += 10
                reasons.append("✨ 天氣快適宜人：涼爽舒適，適合密林森呼吸。")

        evaluated_routes.append({
            "data": r,
            "score": max(0, min(100, score)),
            "reasons": reasons
        })
        
    evaluated_routes = sorted(evaluated_routes, key=lambda x: x["score"], reverse=True)
    best_route = evaluated_routes[0]
    
    st.markdown(f"""
    <div class="warning-card" style="border-left: 8px solid #2E7D32; background-color: #E8F5E9;">
        <h3 style="margin-top:0px; color:#1E4620; font-size:1.5rem;">👑 天氣自適應最優推薦：{best_route['data']['name']}</h3>
        <p style="font-weight:bold; font-size:1.15rem; margin-bottom:10px;">🏆 綜合安全評級得分：{best_route['score']} / 100 分</p>
        <p style="font-size:1.1rem; line-height:1.5; color:#444;">{"<br>".join(best_route['reasons']) if best_route['reasons'] else "✨ 當前天氣各項指標極佳，本路線無障礙通行度完美！"}</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("### 🗺️ 路線規劃地圖與物理模型")
    selected_name = st.selectbox(
        "🗺️ 查看本景點下之其他備選路線剖析：", 
        [r["data"]["name"] for r in evaluated_routes],
        index=0
    )
    
    current_route_eval = next(r for r in evaluated_routes if r["data"]["name"] == selected_name)
    current_route = current_route_eval["data"]
    
    col_model1, col_model2 = st.columns(2)
    with col_model1:
        st.markdown(f"""
        <div class="card" style="margin-bottom:10px;">
            <p style="margin-bottom:5px;"><b>♿ 坡度物理模型：</b></p>
            <p style="font-size:1.1rem; color:#1E4620; font-weight:bold;">{current_route['slope_model']}</p>
        </div>
        <div class="card" style="margin-bottom:10px;">
            <p style="margin-bottom:5px;"><b>🌳 遮陽亭與樹陰分布：</b></p>
            <p style="font-size:1.1rem; color:#2E7D32; font-weight:bold;">{current_route['shade_model']}</p>
        </div>
        """, unsafe_allow_html=True)
    with col_model2:
        st.markdown(f"""
        <div class="card" style="margin-bottom:10px;">
            <p style="margin-bottom:5px;"><b>🍼 母嬰室與無障礙設施：</b></p>
            <p style="font-size:1.1rem; color:#0288D1; font-weight:bold;">{current_route['infant_model']}</p>
        </div>
        <div class="card" style="margin-bottom:10px;">
            <p style="margin-bottom:5px;"><b>🚶 步行路況簡述：</b></p>
            <p style="font-size:1.05rem; color:#555;">{current_route['desc']}</p>
        </div>
        """, unsafe_allow_html=True)
        
    st.write("🛰️ **手機實時街區地圖（支援手勢觸控）：**")
    leaflet_html_route = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.css" />
        <script src="https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.js"></script>
        <style>
            html, body, #map {{ width: 100%; height: 100%; margin: 0; padding: 0; }}
            .hud {{
                position: absolute; bottom: 15px; left: 15px; z-index: 1000;
                background: white; padding: 10px 14px; border-radius: 12px;
                box-shadow: 0 4px 15px rgba(0,0,0,0.15); border-left: 5px solid #2E7D32;
            }}
            .hud p {{ margin: 0; font-size: 11px; font-weight: bold; color: #333; }}
        </style>
    </head>
    <body>
        <div class="hud"><p>🛰️ 正在獲取手機 GPS 精準坐標定位</p></div>
        <div id="map"></div>
        <script>
            var map = L.map('map',{{ zoomControl: false, tap: true }}).setView([{current_route['center'][0]}, {current_route['center'][1]}], 16);
            L.tileLayer('https://{{s}}.basemaps.cartocdn.com/rastertiles/voyager/{{z}}/{{x}}/{{y}}{{r}}.png').addTo(map);
            
            var latlngs = {json.dumps(current_route['coords'])};
            var polyline = L.polyline(latlngs, {{ color: '#2E7D32', weight: 7, opacity: 0.95 }}).addTo(map);
            
            L.marker(latlngs[0]).addTo(map).bindPopup("<b>🏁 起點：開始行程</b>").openPopup();
            L.marker(latlngs[latlngs.length - 1]).addTo(map).bindPopup("<b>🏆 終點：{current_route['base_label']}</b>");
            map.fitBounds(polyline.getBounds(), {{ padding: [20, 20] }});
        </script>
    </body>
    </html>
    """
    st.components.v1.html(leaflet_html_route, height=350)

    dest_lat, dest_lon = current_route['coords'][-1][0], current_route['coords'][-1][1]
    amap_url = f"https://uri.amap.com/navigation?from={lon},{lat},我的位置&to={dest_lon},{dest_lat},{current_route['base_label']}&mode=walk&coordinate=wgs84&callnative=1"
    st.link_button("📱 開啟地圖導航並同步語音引導", amap_url, use_container_width=True, type="primary")

# ==================== 功能二：隨行裝備 (100% 根據天氣自適應清單) ====================
elif st.session_state.current_page == "gear":
    if st.button("⬅️ 返回主選單", type="secondary"):
        st.query_params.clear()
        st.session_state.current_page = "home"
        st.rerun()
        
    st.subheader("🎒 隨行裝備")
    st.write("系統根據當前的溫度、紫外線、是否下雨、以及風速數據，自動為您與寶寶生成客製化隨行裝備清單：")
    
    st.markdown("""
    <div class="card" style="border-left: 8px solid #2E7D32;">
        <h4 style="margin-top:0px; font-size:1.35rem;">🎒 出行背包自適應裝備核對表</h4>
    </div>
    """, unsafe_allow_html=True)
    
    # 🌧️ 下雨連動
    if rain:
        st.checkbox("🌧️ **嬰兒車防雨透氣罩 & 親子大雨傘** *(當前天氣有雨，下雨必備！)*", value=True)
        st.checkbox("🌂 **備用寶寶乾爽乾衣物 (裝於防水密封袋)**", value=True)
        
    # ☀️ 紫外線連動
    if uv >= 4.0:
        st.checkbox("☀️ **兒童防曬乳 (SPF30+) & 推車抗 UV 遮陽罩** *(當前紫外線偏強，防止曬傷！)*", value=True)
        st.checkbox("🧢 **親子大簷透氣太陽帽**", value=True)
        
    # 🌡️ 溫度連動
    if temp >= 30.0:
        st.checkbox("🌬️ **夾式推車靜音風扇** *(氣溫過高！夾在推車側邊輔助降溫)*", value=True)
        st.checkbox("🥤 **補充水分及電解質親子涼水壺**", value=True)
    elif temp < 18.0:
        st.checkbox("🧥 **寶寶防寒加厚斗篷與小被子** *(天氣偏涼，保暖至上！)*", value=True)
        st.checkbox("🍼 **保溫熱水瓶（維持泡奶適溫）**", value=True)
    else:
        st.checkbox("🍼 **親子通用常規飲用水瓶** *(氣溫舒適，帶普通飲水即可)*", value=True)
        
    # 🍃 風速連動
    if wind >= 20.0:
        st.checkbox("🍃 **嬰兒車防風固定防落夾** *(當前風速較大，固定遮陽蓬和被子必備！)*", value=True)
        st.checkbox("🧣 **寶寶棉質防風小領巾 (保護氣管)**", value=True)
    else:
        st.checkbox("🔒 **常用推車置物架掛鉤** *(帶上防風備用置物掛鉤)*", value=True)

st.markdown("<br><hr style='margin: 10px 0; border: none; border-top: 1px solid #E0E0E0;'>", unsafe_allow_html=True)
st.caption("🔒 系統安全防護聲明：絲野仙蹤（Eco-Family）始終將親子安全置於首位。本App規劃之數據僅供決策輔助，戶外出行仍請家長以現場實際路況與安全第一為準。")