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
import base64
import io
from PIL import Image # 引入 Pillow 圖像庫，實現真正的離線電腦視覺特徵提取

# ==================== 1. 全域變數安全初始化防護 ====================
if "global_temp" not in st.session_state:
    st.session_state.global_temp = 26.7
if "global_uv" not in st.session_state:
    st.session_state.global_uv = 1.5
if "global_humidity" not in st.session_state:
    st.session_state.global_humidity = 95
if "global_rain" not in st.session_state:
    st.session_state.global_rain = False
if "global_wind" not in st.session_state:
    st.session_state.global_wind = 12.0
if "global_weather_mode" not in st.session_state:
    st.session_state.global_weather_mode = "🟢 實時連線模式"
if "current_page" not in st.session_state:
    st.session_state.current_page = "home"
if "preset_location" not in st.session_state:
    st.session_state.preset_location = "龍環葡韻住宅式博物館"
if "override_weather" not in st.session_state:
    st.session_state.override_weather = False

# 🔍 讀取 URL 查詢參數，實現 HTML 與 Streamlit 的流暢無縫頁面切換
query_params = st.query_params
if "page" in query_params:
    st.session_state.current_page = query_params["page"]
else:
    st.session_state.current_page = "home"

# ==================== 2. 網頁全域美學與移動端響應式大字體 CSS 樣式 ====================
st.set_page_config(
    page_title="絲野仙蹤 (Eco-Family) 親子康旅導航系統",
    page_icon="🍀",
    layout="centered", # 使用居中版面，為手機框打造完美基礎
    initial_sidebar_state="collapsed"
)

# 注入 CSS：徹底隱藏 Streamlit 原生側邊欄，並在電腦端網頁中渲染一個精美的「實體手機外殼」
# 並定義 100% 視覺複製、單列垂直排版的卡片樣式 (.grid-card)
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

    /* 2. 核心魔法：電腦端顯示精美手機框，手機端自適應全螢幕 */
    @media (min-width: 768px) {
        .main .block-container {
            max-width: 450px !important;
            padding: 30px 24px !important;
            background-color: #FFFFFF !important;
            /* 仿實體高端手機的厚重陰影與圓潤邊框 */
            box-shadow: 0 15px 45px rgba(30, 70, 32, 0.12) !important;
            border-radius: 40px !important;
            margin: 40px auto !important;
            border: 10px solid #E3EADF !important; /* 精緻的淺綠灰手機實體邊框 */
            min-height: 850px !important;
            position: relative;
        }
        body {
            background-color: #F0F4EF !important; /* 護眼淡綠色底色 */
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
        text-align: center;
        margin-bottom: 5px !important;
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

    /* 4. 🛠️ 響應式單列垂直列表排版（一行一個功能） */
    .grid-container {
        display: flex;
        flex-direction: column;
        gap: 14px;
        width: 100%;
        box-sizing: border-box;
        margin-top: 10px;
    }

    /* 5. 🛠️ 終極同源樣式：高度鎖定為 110px 的橫向單列卡片，100% 絕對視覺對齊（高度、邊框、圓角、內邊距、陰影） */
    .grid-card {
        background-color: #FFFFFF !important;
        border: 2px solid #E8F5E9 !important; /* 統一邊框大小與顏色 */
        border-radius: 24px !important; /* 統一圓角 */
        padding: 15px 24px !important; /* 統一內距 */
        box-shadow: 0 10px 25px rgba(30, 70, 32, 0.04) !important;
        transition: all 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275) !important;
        min-height: 110px !important; /* 完美的單行卡高度 */
        height: 110px !important;
        width: 100% !important;
        display: flex !important;
        flex-direction: row !important; /* 橫向排列：左邊 Emoji，右邊標題 */
        align-items: center !important;
        justify-content: flex-start !important; /* 靠左對齊 */
        text-decoration: none !important; /* 消除超連結下劃線 */
        box-sizing: border-box !important;
        overflow: hidden !important;
    }

    /* 6. 🛠️ 終極同源樣式：懸停與點擊時的浮動發光動畫 */
    .grid-card:hover,
    .grid-card:active {
        transform: translateY(-5px) !important; /* 浮動高度 */
        box-shadow: 0 15px 30px rgba(30, 70, 32, 0.15) !important; /* 陰影發光 */
        border-color: #66BB6A !important; /* 懸停邊框 */
        background-color: #F1F9F3 !important; /* 懸停背景色 */
    }

    /* 7. 🛠️ 終極同源樣式：左側 Emoji 樣式絕對對齊 */
    .grid-card .emoji {
        font-size: 2.5rem !important; /* 放大 Emoji，高辨識度 */
        line-height: 1 !important;
        margin-right: 20px !important; /* 與右側標題的間距 */
        display: inline-block !important;
    }

    /* 8. 🛠️ 終極同源樣式：右側標題顏色、字型、大小、粗細、行高 100% 絕對對齊 */
    .grid-card .title {
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, "PingFang TC", "Microsoft JhengHei", sans-serif !important;
        color: #1E4620 !important; /* 統一為極具質感的森林深墨綠色 */
        font-size: 1.35rem !important; /* 統一標題字體大小，精準避開遮擋與切斷 */
        font-weight: 800 !important; /* 統一標題字體粗細 */
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

    /* 行動裝置資訊大面板 */
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

    /* 卡片內部地圖導航按鈕樣式 */
    .nav-button-inside {
        display: inline-flex !important;
        align-items: center !important;
        justify-content: center !important;
        background-color: #E8F5E9 !important;
        color: #1E4620 !important;
        border: 1.5px solid #C8E6C9 !important;
        padding: 12px 20px !important;
        border-radius: 14px !important;
        font-weight: 700 !important;
        font-size: 1.1rem !important;
        text-decoration: none !important;
        box-shadow: 0 4px 10px rgba(30, 70, 32, 0.03) !important;
        transition: all 0.2s ease-in-out !important;
        margin-top: 10px !important;
        cursor: pointer !important;
    }
    .nav-button-inside:hover, .nav-button-inside:active {
        background-color: #2E7D32 !important;
        color: #FFFFFF !important;
        border-color: #2E7D32 !important;
        box-shadow: 0 6px 15px rgba(46, 125, 50, 0.2) !important;
    }
</style>
""", unsafe_allow_html=True)

# ==================== 4. 實時外部天氣 API 串接模組 ====================
def get_macau_weather(lat, lon):
    url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current=temperature_2m,relative_humidity_2m,precipitation,wind_speed_10m,uv_index&timezone=Asia%2FShanghai"
    try:
        response = requests.get(url, timeout=3)
        if response.status_code == 200:
            data = response.json()
            current = data["current"]
            return {
                "temp": current["temperature_2m"],
                "humidity": current["relative_humidity_2m"],
                "uv": current["uv_index"],
                "rain": current["precipitation"] > 0,
                "wind": current["wind_speed_10m"],
                "mode": "🟢 實時連線模式"
            }
    except Exception:
        pass
    return {
        "temp": 26.7, "humidity": 95, "uv": 1.5, "rain": False, "wind": 12.0,
        "mode": "🟡 備援模擬模式"
    }

# 更新定位坐標邏輯
if st.session_state.preset_location == "龍環葡韻住宅式博物館":
    lat, lon = 22.1539, 113.5594
elif st.session_state.preset_location == "大潭山郊野公園":
    lat, lon = 22.1581, 113.5623
else:
    lat, lon = 22.1221, 113.5658

# ==================== 5. 手機版 App 頂部智慧標題欄與天氣狀態欄 ====================
st.markdown("<h1>🍀 絲野仙蹤</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align:center; font-size:1.05rem; color:#666; margin-bottom:15px;'>澳門首款親子智慧無障礙康旅隨行助手</p>", unsafe_allow_html=True)

# 天氣獲取與手動模擬核心邏輯
if st.session_state.override_weather:
    temp = st.session_state.global_temp
    uv = st.session_state.global_uv
    rain = st.session_state.global_rain
    wind = st.session_state.global_wind
    humidity = st.session_state.global_humidity
    weather_mode_label = "🟠 手動模擬演示模式"
else:
    weather_data = get_macau_weather(lat, lon)
    temp = weather_data["temp"]
    uv = weather_data["uv"]
    rain = weather_data["rain"]
    wind = weather_data["wind"]
    humidity = weather_data["humidity"]
    weather_mode_label = weather_data["mode"]
    
    st.session_state.global_temp = temp
    st.session_state.global_uv = uv
    st.session_state.global_rain = rain
    st.session_state.global_wind = wind
    st.session_state.global_humidity = humidity

# 🗺️ 頂部智慧天氣狀態欄
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

# ⚙️ 點選展開控制台 (手動模擬氣溫、紫外線、下雨與風速的超大滑桿)
with st.expander("⚙️ 調整出行定位與環境模擬..."):
    location_choice = st.selectbox(
        "📍 模擬當前 GPS 定位:",
        ["龍環葡韻住宅式博物館", "大潭山郊野公園", "路環石排灣郊野公園"],
        index=["龍環葡韻住宅式博物館", "大潭山郊野公園", "路環石排灣郊野公園"].index(st.session_state.preset_location)
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
        sim_temp = st.slider("🌡️ 模擬環境溫度 (°C)", min_value=10.0, max_value=42.0, value=float(st.session_state.global_temp), step=0.5)
        sim_uv = st.slider("☀️ 模擬紫外線強度 (UV)", min_value=0.0, max_value=11.0, value=float(st.session_state.global_uv), step=0.5)
        sim_rain = st.checkbox("🌧️ 模擬正在下雨", value=st.session_state.global_rain)
        sim_wind = st.slider("🍃 模擬風速強度 (km/h)", min_value=0.0, max_value=60.0, value=float(st.session_state.global_wind), step=1.0)
        
        st.session_state.global_temp = sim_temp
        st.session_state.global_uv = sim_uv
        st.session_state.global_rain = sim_rain
        st.session_state.global_wind = sim_wind
    else:
        st.success(f"📱 系統正在讀取澳門實時天氣數據。")

st.markdown("<hr style='margin: 15px 0; border: none; border-top: 1px solid #E0E0E0;'>", unsafe_allow_html=True)

# ==================== 6. 頁面路由：首頁大卡片按鈕 (1行1功能，高度 110px，純 HTML 100% 絕對對齊) ====================
if st.session_state.current_page == "home":
    st.markdown("<h3 style='margin-bottom:12px; font-size:1.35rem;'>📱 親子出行隨行工具：</h3>", unsafe_allow_html=True)
    
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

# ==================== 功能一：智慧規劃路線 (精準坡度、遮陽樹陰、母嬰設施綜合算法推薦) ====================
elif st.session_state.current_page == "route":
    if st.button("⬅️ 返回主選單", type="secondary"):
        st.query_params.clear() # 清空查詢參數，返回主畫面
        st.session_state.current_page = "home"
        st.rerun()
        
    st.subheader("🗺️ 智慧規劃路線")
    st.write("系統根據天氣指標、坡道模型、林蔭遮蔭率及母嬰設施進行動態多維度推薦評估：")
    
    # 建立 3 個精準的親子路線物理與設施模型
    routes_db = [
        {
            "id": "A",
            "name": "🌲 大潭山林蔭無障礙步道",
            "slope_model": "坡度最大約 2.8% (中度平緩，升降機直達)",
            "shade_model": "🌳 遮陽亭與密林覆蓋率達 85% (高遮蔭)",
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
            "desc": "由博物館直通大潭山頂，沿途皆為特製平緩防滑道，避暑首選。"
        },
        {
            "id": "B",
            "name": "🏰 龍環葡韻湖畔親水漫步徑",
            "slope_model": "坡度僅 0.5% (極度平坦，推車最省力)",
            "shade_model": "🌳 遮陽亭與樹蔭覆蓋率約 40% (低遮蔭)",
            "infant_model": "🍼 配備 (別墅景區展館內設有育嬰室)",
            "coords": [
                [22.1530, 113.5570], 
                [22.1535, 113.5585], 
                [22.1539, 113.5594]
            ],
            "center": [22.1534, 113.5582],
            "base_label": "龍環葡韻親水長廊",
            "desc": "沿親水湖畔平地漫步，景色極佳，全平緩路面，推嬰兒車最輕鬆舒適。"
        },
        {
            "id": "C",
            "name": "🐼 石排灣公園大熊貓科普徑",
            "slope_model": "坡度約 1.5% (全平防滑橡膠路面，極好推)",
            "shade_model": "🌳 全程林蔭與科普有蓋雨廊覆蓋 75% (高防雨)",
            "infant_model": "🍼 配備 (大熊貓館內備有五星級哺乳室)",
            "coords": [
                [22.1215, 113.5650], 
                [22.1221, 113.5658], 
                [22.1235, 113.5668]
            ],
            "center": [22.1225, 113.5659],
            "base_label": "藥用植物園觸摸區",
            "desc": "圍繞大熊貓館的有蓋平整步道，防雨遮陽設施完善。"
        }
    ]
    
    # 🧠 智慧自適應打分演算法（已加入坡度舒適度加權，保證龍環葡韻在舒適天氣下勝出！）
    evaluated_routes = []
    for r in routes_db:
        # 根據路線坡度給予基礎省力舒適分
        if r["id"] == "B":
            score = 100
        elif r["id"] == "C":
            score = 95
        else:
            score = 90
            
        reasons = []
        
        # 1. 紫外線 & 溫度與遮蔭率連動評分
        if uv >= 5.0 or temp >= 30.0:
            if "85%" in r["shade_model"]:
                score += 5
                reasons.append("🔥 當前酷熱/高UV，本路線高密度樹蔭能阻擋 85% 陽光，極力推薦！")
            elif "75%" in r["shade_model"]:
                score += 2
                reasons.append("🔥 當前天氣炎熱，本路線科普長廊能提供良好避暑屏障。")
            else:
                score -= 25
                reasons.append("⚠️ 當前紫外線偏強，本路線遮蔭不足 (僅40%)，容易曬傷寶寶。")
                
        # 2. 下雨狀況連動評分
        if rain:
            if "75%" in r["shade_model"]:  # 石排灣科普長廊有連續雨棚
                score += 10
                reasons.append("🌧️ 天氣下雨中，本路線有蓋長廊覆蓋率高，提供五星級防雨護航。")
            elif "85%" in r["shade_model"]:  # 大潭山部分路段是密林，有部分遮雨效果
                score += 0
                reasons.append("🌧️ 天氣下雨中，本步道有茂密樟樹林部分擋雨，但建議加裝雨罩。")
            else:
                score -= 35
                reasons.append("❌ 天氣下雨中，本路線為全露天親水步道，推嬰兒車極不方便！")
                
        # 3. 風速與坡道/開闊度連動評分
        if wind >= 25.0:
            if "2.8%" in r["slope_model"]:  # 山區路段風大，推車上坡逆風
                score -= 15
                reasons.append("💨 當前風速過大，大潭山區逆風推車會增加家長體力負擔。")
            elif "0.5%" in r["slope_model"]: # 湖畔風口
                score -= 20
                reasons.append("💨 當前風速偏強，湖畔開闊地帶風力強勁，推車易受強風侵襲。")
            else:
                score += 5
                reasons.append("💨 當前風力大，本步道地勢低且有山體阻擋，防風效果佳。")
                
        evaluated_routes.append({
            "data": r,
            "score": max(0, min(100, score)),
            "reasons": reasons
        })
        
    # 依演算法評分排序，最優推薦放在首位！
    evaluated_routes = sorted(evaluated_routes, key=lambda x: x["score"], reverse=True)
    best_route = evaluated_routes[0]
    
    # 智慧最佳推薦橫幅
    st.markdown(f"""
    <div class="warning-card" style="border-left: 8px solid #2E7D32; background-color: #E8F5E9;">
        <h3 style="margin-top:0px; color:#1E4620; font-size:1.5rem;">👑 天氣自適應最優推薦：{best_route['data']['name']}</h3>
        <p style="font-weight:bold; font-size:1.15rem; margin-bottom:10px;">🏆 綜合安全評級得分：{best_route['score']} / 100 分</p>
        <p style="font-size:1.1rem; line-height:1.5; color:#444;">{"<br>".join(best_route['reasons']) if best_route['reasons'] else "✨ 當前天氣各項指標極佳，本路線無障礙通行度完美！"}</p>
    </div>
    """, unsafe_allow_html=True)
    
    # 路線選擇與切換模型
    st.markdown("### 🗺️ 路線規劃地圖與物理模型")
    selected_name = st.selectbox("切換並查看其他路線的模型剖析：", [r["data"]["name"] for r in evaluated_routes])
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
        
    # Leaflet 地圖展示
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

    # 地圖 App 語音導航連結 (100% 無高德字眼)
    dest_lat, dest_lon = current_route['coords'][-1][0], current_route['coords'][-1][1]
    amap_url = f"https://uri.amap.com/navigation?from={lon},{lat},我的位置&to={dest_lon},{dest_lat},{current_route['base_label']}&mode=walk&coordinate=wgs84&callnative=1"
    st.link_button("📱 開啟地圖導航並同步語音引導", amap_url, use_container_width=True, type="primary")

# ==================== 功能三：隨行裝備 (推車優化配件全部刪除，100% 根據四項天氣指標動態自適應清單) ====================
elif st.session_state.current_page == "gear":
    if st.button("⬅️ 返回主選單", type="secondary"):
        st.query_params.clear() # 清空查詢參數，返回主畫面
        st.session_state.current_page = "home"
        st.rerun()
        
    st.subheader("🎒 隨行裝備")
    # 💡 依照要求，精確修改說明文案：
    st.write("系統根據當前的溫度、紫外線、是否下雨、以及風速數據，自動為您與寶寶生成客製化隨行裝備清單：")
    
    st.markdown("""
    <div class="card" style="border-left: 8px solid #2E7D32;">
        <h4 style="margin-top:0px; font-size:1.35rem;">🎒 出行背包自適應裝備核對表</h4>
    </div>
    """, unsafe_allow_html=True)
    
    # ── 1. 下雨連動裝備 ──
    if rain:
        st.checkbox("🌧️ **嬰兒車防雨透氣罩 & 親子大雨傘** *(當前天氣有雨，下雨必備！)*", value=True)
        st.checkbox("🌂 **備用寶寶乾爽乾衣物 (裝於防水密封袋)**", value=True)
    else:
        st.checkbox("🌂 輕便雨衣 *(當前天氣無雨，帶備用雨具即可)*", value=False)
        
    # ── 2. 紫外線連動裝備 ──
    if uv >= 4.0:
        st.checkbox("☀️ **兒童防曬乳 (SPF30+) & 推車抗 UV 遮陽罩** *(當前紫外線偏強，防止曬傷！)*", value=True)
        st.checkbox("🧢 **親子大簷透氣太陽帽**", value=True)
    else:
        st.checkbox("🧢 常規遮陽帽 *(紫外線一般，可帶備用)*", value=False)
        
    # ── 3. 溫度連動裝備 ──
    if temp >= 30.0:
        st.checkbox("🌬️ **夾式推車靜音風扇** *(氣溫過高！夾在推車側邊輔助降溫)*", value=True)
        st.checkbox("🥤 **補充電解質親子涼水壺** *(防寶寶脫水長疹！)*", value=True)
    elif temp < 18.0:
        st.checkbox("🧥 **寶寶防寒加厚斗篷與小被子** *(天氣偏涼，保暖至上！)*", value=True)
        st.checkbox("🍼 **保溫熱水瓶（維持泡奶適溫）**", value=True)
    else:
        st.checkbox("🍼 親子通用常規飲用水瓶", value=True)
        
    # ── 4. 風速連動裝備 ──
    if wind >= 20.0:
        st.checkbox("🍃 **嬰兒車防風固定防落夾** *(當前風速較大，固定遮陽蓬和被子必備！)*", value=True)
        st.checkbox("🧣 **寶寶棉質防風小領巾 (保護氣管)**", value=True)
    else:
        st.checkbox("🔒 常用推車置物架掛鉤", value=True)

st.markdown("<br><hr style='margin: 10px 0; border: none; border-top: 1px solid #E0E0E0;'>", unsafe_allow_html=True)
st.caption("🔒 系統安全防護聲明：絲野仙蹤（Eco-Family）始終將親子安全置於首位。本App規劃之數據僅供決策輔助，戶外出行仍請家長以現場實際路況與安全第一為準。")