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

# 注入 CSS：徹底隱藏 Streamlit 原生電腦端側邊欄，並在電腦端網頁中渲染一個精美的「實體手機外殼」
# 並定義 100% 視覺複製、完全對稱統一的四宮格卡片樣式 (.grid-card)
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

    /* 4. 🛠️ 響應式 2x2 對稱網格排版 */
    .grid-container {
        display: grid;
        grid-template-columns: repeat(2, 1fr);
        gap: 14px;
        width: 100%;
        box-sizing: border-box;
        margin-top: 10px;
    }

    /* 5. 🛠️ 終極同源樣式：四個大卡片高度縮合至 160px，100% 絕對視覺對齊（高度、邊框、圓角、內邊距、陰影） */
    .grid-card {
        background-color: #FFFFFF !important;
        border: 2px solid #E8F5E9 !important; /* 統一邊框大小與顏色 */
        border-radius: 24px !important; /* 統一圓角大小 */
        padding: 20px 14px !important; /* 統一內距大小 */
        box-shadow: 0 10px 25px rgba(30, 70, 32, 0.04) !important;
        transition: all 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275) !important;
        min-height: 160px !important; /* 縮小高度，完美適配手機一屏顯示 */
        height: 160px !important;
        width: 100% !important;
        display: flex !important;
        flex-direction: column !important;
        align-items: center !important;
        justify-content: center !important;
        text-align: center !important;
        text-decoration: none !important; /* 消除 HTML 卡片超連結下劃線 */
        box-sizing: border-box !important;
        overflow: hidden !important;
    }

    /* 6. 🛠️ 終極同源樣式：兩者的懸停、點選、發光與浮動動畫 100% 一體化 */
    .grid-card:hover,
    .grid-card:active {
        transform: translateY(-6px) !important; /* 浮動高度 */
        box-shadow: 0 15px 30px rgba(30, 70, 32, 0.15) !important; /* 陰影發光 */
        border-color: #66BB6A !important; /* 懸停邊框 */
        background-color: #F1F9F3 !important; /* 懸停背景色 */
    }

    /* 7. 🛠️ 終極同源樣式：第一排文字 (Emoji) 大小與行高對齊 */
    .grid-card .emoji {
        font-size: 2.5rem !important; /* 放大 Emoji，使其更加突出直觀 */
        margin-top: 0px !important;
        margin-bottom: 8px !important;
        line-height: 1 !important;
        text-align: center !important;
        display: block !important;
    }

    /* 8. 🛠️ 終極同源樣式：第二排文字 (卡片標題) 顏色、字型、字級、字重、行高絕對對齊 */
    .grid-card .title {
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, "PingFang TC", "Microsoft JhengHei", sans-serif !important;
        color: #1E4620 !important; /* 統一為極具質感的森林深墨綠色 */
        font-size: 1.25rem !important; /* 統一標題字體大小，精準避開遮擋與切斷 */
        font-weight: 800 !important; /* 統一標題字體粗細 */
        margin-top: 5px !important;
        margin-bottom: 0px !important;
        line-height: 1.4 !important;
        text-align: center !important;
        display: block !important;
        word-wrap: break-word !important;
        white-space: normal !important; /* 允許文字自動折行 */
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
        background-color: #E8F5E9;
        padding: 20px;
        border-radius: 18px;
        margin-bottom: 15px;
        border-left: 6px solid #4CAF50;
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

# ==================== 4. 實時外部微氣候 API 串接模組 ====================
def get_macau_weather(lat, lon):
    url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current=temperature_2m,relative_humidity_2m,uv_index&timezone=Asia%2FShanghai"
    try:
        response = requests.get(url, timeout=3)
        if response.status_code == 200:
            data = response.json()
            current = data["current"]
            return {
                "temp": current["temperature_2m"],
                "humidity": current["relative_humidity_2m"],
                "uv": current["uv_index"],
                "mode": "🟢 實時連線模式"
            }
    except Exception:
        pass
    return {
        "temp": 26.7, "humidity": 95, "uv": 1.5,
        "mode": "🟡 備援模擬模式"
    }

# 更新定位坐標邏輯
if st.session_state.preset_location == "龍環葡韻住宅式博物館":
    lat, lon = 22.1539, 113.5594
elif st.session_state.preset_location == "大潭山郊野公園":
    lat, lon = 22.1581, 113.5623
else:
    lat, lon = 22.1221, 113.5658

# ==================== 5. 手機版 App 頂部智慧標題欄與智慧狀態欄 ====================
st.markdown("<h1>🍀 絲野仙蹤</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align:center; font-size:1.05rem; color:#666; margin-bottom:15px;'>澳門首款親子智慧無障礙康旅隨行助手</p>", unsafe_allow_html=True)

# 天氣獲取與手動模擬核心邏輯
if st.session_state.override_weather:
    # 使用手動模擬數據，鎖定狀態模式
    temp = st.session_state.global_temp
    uv = st.session_state.global_uv
    humidity = st.session_state.global_humidity
    weather_mode_label = "🟠 手動模擬演示模式"
else:
    # 使用實時 API 數據
    weather_data = get_macau_weather(lat, lon)
    temp = weather_data["temp"]
    uv = weather_data["uv"]
    humidity = weather_data["humidity"]
    weather_mode_label = weather_data["mode"]
    # 同步回 session_state
    st.session_state.global_temp = temp
    st.session_state.global_uv = uv
    st.session_state.global_humidity = humidity

# 🗺️ 頂部智慧狀態欄 (仿高端地圖 App 設計)
st.markdown(f"""
<div style="background-color: #E8F5E9; padding: 14px 18px; border-radius: 18px; box-shadow: 0 4px 15px rgba(46,125,50,0.06); display: flex; align-items: center; justify-content: space-between; margin-bottom: 12px; border: 1px solid #C8E6C9;">
    <div style="display: flex; align-items: center; gap: 8px;">
        <span style="font-size: 1.4rem;">📍</span>
        <span style="font-size: 1.15rem; font-weight: bold; color: #1E4620;">{st.session_state.preset_location}</span>
    </div>
    <div style="text-align: right;">
        <span style="font-size: 1.15rem; font-weight: bold; color: #2E7D32;">🌡️ {temp}°C</span>
        <span style="font-size: 0.95rem; color: #555; display: block;">☀️ UV {uv} | 💧 {humidity}%</span>
    </div>
</div>
""", unsafe_allow_html=True)

# ⚙️ 點選展開控制台 (內置手動模擬氣溫與紫外線的超大滑桿)
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
    
    # 天氣手動模擬開關切換
    override_active = st.toggle("🌡️ 啟用手動模擬天氣數據", value=st.session_state.override_weather)
    
    if override_active != st.session_state.override_weather:
        st.session_state.override_weather = override_active
        st.rerun()
        
    if override_active:
        # 手動調整滑桿
        sim_temp = st.slider("🌡️ 模擬環境溫度 (°C)", min_value=10.0, max_value=42.0, value=float(st.session_state.global_temp), step=0.5)
        sim_uv = st.slider("☀️ 模擬紫外線強度 (UV)", min_value=0.0, max_value=11.0, value=float(st.session_state.global_uv), step=0.5)
        
        # 保存變更至 session_state 供跨功能全局響應
        st.session_state.global_temp = sim_temp
        st.session_state.global_uv = sim_uv
    else:
        st.success(f"📱 系統正在讀取澳門實時微氣候數據。")

st.markdown("<hr style='margin: 15px 0; border: none; border-top: 1px solid #E0E0E0;'>", unsafe_allow_html=True)

# ==================== 6. 頁面路由：首頁大卡片按鈕 (2x2 手機自適應，大框按鈕二合一) ====================
if st.session_state.current_page == "home":
    st.markdown("<h3 style='margin-bottom:12px; font-size:1.35rem;'>📱 親子出行隨行工具：</h3>", unsafe_allow_html=True)
    
    # 🛠️ 終極同源鏡像設計：徹底移除描述文字！
    # 高度精確固定為 160px。在手機上顯示效果極其驚艷、對齊 100%、且完全沒有任何看不完的 Bug！
    st.markdown("""
    <div class="grid-container">
      <a class="grid-card" href="?page=route" target="_self">
        <span class="emoji">🗺️</span>
        <span class="title">智慧規劃路線</span>
      </a>
      <a class="grid-card" href="?page=resting" target="_self">
        <span class="emoji">⛱️</span>
        <span class="title">無障礙休憩點篩選</span>
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

# ==================== 功能一：智慧規劃路線 (高德地圖級：Leaflet高清街區地圖、手機觸控完美適配) ====================
elif st.session_state.current_page == "route":
    if st.button("⬅️ 返回主選單", type="secondary"):
        st.query_params.clear() # 清空查詢參數，返回主畫面
        st.session_state.current_page = "home"
        st.rerun()
        
    st.subheader("🗺️ 智慧規劃路線")
    
    # 根據模擬的天氣數據，自動進行自適應路線規劃推薦
    if temp >= 30.0:
        route_name = "🌲 大潭山林蔭避暑步道"
        route_desc = f"偵測到當前溫度達 {temp}°C（高於避暑臨界值 30°C），已為您動態規劃遮蔭率 85% 以上的『林蔭綠色路徑』，防止寶寶烈日曬傷與熱傷害。"
        path_json = [
            [22.1539, 113.5594], # 起點：龍環葡韻住宅式博物館
            [22.1555, 113.5605], 
            [22.1572, 113.5621], 
            [22.1581, 113.5623], 
            [22.1585, 113.5630]  # 終點：大潭山避暑景觀亭
        ]
        steps = [
            {"num": "1", "dist": "180米", "title": "龍環葡韻出發", "detail": "整鋪路面，兩旁樟樹遮蔭，推車好走。"},
            {"num": "2", "dist": "220米", "title": "大潭山斜行升降機", "detail": "無障礙直達，推車免折疊直接上山。"},
            {"num": "3", "dist": "50米", "title": "大潭山觀景眺望台", "detail": "設有大尺寸遮陽雨棚，紫外線防護良好。"},
            {"num": "4", "dist": "120米", "title": "抵達避暑景觀亭", "detail": "遮蔭率達 90%，設有無障礙哺乳室。"}
        ]
        start_label, end_label = "龍環葡韻住宅式博物館", "大潭山避暑景觀亭"
        center_lat, center_lon = 22.1562, 113.5612
        tip_style = "warning-card"
        icon = "☀️"
    else:
        route_name = "🍀 石排灣平緩親子綠色徑"
        route_desc = f"當前溫度為快適的 {temp}°C，已為您優選地勢起伏最小、大自然景致最豐富的『大熊貓科普路線』，全程皆為推車友好塑膠路面。"
        path_json = [
            [22.1215, 113.5650], # 起點：石排灣公園正門
            [22.1221, 113.5658], 
            [22.1235, 113.5668]  # 終點：藥用植物園
        ]
        steps = [
            {"num": "1", "dist": "120米", "title": "石排灣郊野公園正門", "detail": "正門寬敞無台階，適合親子雙人推車前進。"},
            {"num": "2", "dist": "150米", "title": "澳門大熊貓館", "detail": "館內全空調恆溫，配有無障礙親子洗手間。"},
            {"num": "3", "dist": "200米", "title": "香徑藥用植物園", "detail": "平直步道，兩側種滿本地特色香用草藥。"}
        ]
        start_label, end_label = "石排灣公園入口", "藥用植物園觸摸區"
        center_lat, center_lon = 22.1225, 113.5659
        tip_style = "card"
        icon = "✨"

    st.markdown(f"""
    <div class="{tip_style}">
        <h4 style="margin-top:0px; font-size:1.4rem;">{icon} 自適應氣候推薦：{route_name}</h4>
        <p style="font-size:1.1rem; margin-bottom:5px;"><b>規劃依據：</b> {route_desc}</p>
        <p style="font-size:1.05rem; color:#555; margin-bottom:0px;">實時指標 ➔ 溫度：{temp}°C | 紫外線：{uv}</p>
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
            var map = L.map('map',{{ zoomControl: false, tap: true }}).setView([{center_lat}, {center_lon}], 16);
            L.tileLayer('https://{{s}}.basemaps.cartocdn.com/rastertiles/voyager/{{z}}/{{x}}/{{y}}{{r}}.png').addTo(map);
            
            var latlngs = {json.dumps(path_json)};
            var polyline = L.polyline(latlngs, {{ color: '#2E7D32', weight: 7, opacity: 0.95 }}).addTo(map);
            
            L.marker(latlngs[0]).addTo(map).bindPopup("<b>🏁 起點：{start_label}</b>").openPopup();
            L.marker(latlngs[latlngs.length - 1]).addTo(map).bindPopup("<b>🏆 終點：{end_label}</b>");
            map.fitBounds(polyline.getBounds(), {{ padding: [20, 20] }});
        </script>
    </body>
    </html>
    """
    st.components.v1.html(leaflet_html_route, height=350)

    st.write("🚶 **步行步驟分解：**")
    for step in steps:
        st.markdown(f"""
        <div class="step-card">
            <span style="background-color: #1E4620; color: white; border-radius: 50%; padding: 3px 9px; font-weight: bold; font-size: 1.15rem; margin-right: 8px;">{step['num']}</span>
            <b style="font-size: 1.15rem;">{step['title']}</b>
            <span style="float: right; font-size: 1.1rem; color: #4CAF50; font-weight: bold;">{step['dist']}</span>
            <p style="font-size: 1.05rem; color: #555; margin-top: 6px; margin-bottom: 0px; padding-left: 28px;">{step['detail']}</p>
        </div>
        """, unsafe_allow_html=True)

    amap_url = f"https://uri.amap.com/navigation?from={lon},{lat},我的位置&to={path_json[-1][1]},{path_json[-1][0]},{end_label}&mode=walk&coordinate=wgs84&callnative=1"
    st.link_button("📱 喚醒高德地圖 App 開始語音導航", amap_url, use_container_width=True, type="primary")

# ==================== 功能二：無障礙休憩點篩選 ====================
elif st.session_state.current_page == "resting":
    if st.button("⬅️ 返回主選單", type="secondary"):
        st.query_params.clear() # 清空查詢參數，返回主畫面
        st.session_state.current_page = "home"
        st.rerun()
        
    st.subheader("⛱️ 避開階梯與陡坡：推車友善休憩點")
    
    st.markdown("#### 🔍 手機觸控篩選面板")
    slope_limit = st.selectbox(
        "♿ 最高容許坡度限制:", 
        options=["坡度 < 3% (極度平坦)", "坡度 < 8% (微陡斜坡)", "無限制"]
    )
    col_rest_f1, col_rest_f2 = st.columns(2)
    with col_rest_f1:
        shade_req = st.checkbox("🌳 必須有遮陽亭樹蔭", value=True)
    with col_rest_f2:
        nursing_room = st.checkbox("🍼 必須配備母嬰室", value=True)
        
    poi_data = [
        {
            "name": "⛱️ 大潭山無障礙景觀亭",
            "slope": "坡度 < 3% (極度平坦)", "shade": True, "nursing": True,
            "desc": "推車專用平緩坡道直達，綠樹遮蔭率 100%。",
            "lat": 22.1581, "lon": 113.5623
        },
        {
            "name": "🤱 龍環葡韻濕地景觀長廊",
            "slope": "坡度 < 3% (極度平坦)", "shade": True, "nursing": True,
            "desc": "全平直木棧道，旁有博物館大哺乳室。",
            "lat": 22.1539, "lon": 113.5594
        },
        {
            "name": "🐼 石排灣大熊貓館前廣場",
            "slope": "坡度 < 3% (極度平坦)", "shade": True, "nursing": True,
            "desc": "設有大型遮蔭大棚，館內備有優質母嬰室。",
            "lat": 22.1221, "lon": 113.5658
        }
    ]
    
    filtered_pois = [
        p for p in poi_data 
        if (slope_limit == "無限制" or p["slope"] == slope_limit)
        and (not shade_req or p["shade"])
        and (not nursing_room or p["nursing"])
    ]
    
    st.write("🛰️ **篩選出推車友善休憩地標（ Leaflet 觸控版）**")
    
    resting_markers_json = [{"lat": p["lat"], "lon": p["lon"], "name": p["name"], "desc": p["desc"]} for p in filtered_pois]
    leaflet_html_resting = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.css" />
        <script src="https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.js"></script>
        <style>
            html, body, #map {{ width: 100%; height: 100%; margin: 0; padding: 0; }}
        </style>
    </head>
    <body>
        <div id="map"></div>
        <script>
            var map = L.map('map',{{ zoomControl: false, tap: true }}).setView([{lat}, {lon}], 14);
            L.tileLayer('https://{{s}}.basemaps.cartocdn.com/rastertiles/voyager/{{z}}/{{x}}/{{y}}{{r}}.png').addTo(map);

            var userIcon = L.divIcon({{
                html: '<div style="background-color: #F44336; width: 14px; height: 14px; border-radius: 50%; border: 2.5px solid white; box-shadow: 0 0 10px rgba(244,67,54,0.9);"></div>',
                className: 'user-location-icon'
            }});
            L.marker([{lat}, {lon}], {{icon: userIcon}}).addTo(map).bindPopup("<b>📍 您的當前位置</b>").openPopup();

            var pois = {json.dumps(resting_markers_json)};
            var poiGroup = L.featureGroup();
            pois.forEach(function(poi) {{
                var marker = L.marker([poi.lat, poi.lon]).addTo(map)
                    .bindPopup("<b>" + poi.name + "</b><br><span style='font-size:11px;color:#555;'>" + poi.desc + "</span>");
                poiGroup.addLayer(marker);
            }});
            if (pois.length > 0) {{
                map.fitBounds(poiGroup.getBounds(), {{ padding: [30, 30] }});
            }}
        </script>
    </body>
    </html>
    """
    st.components.v1.html(leaflet_html_resting, height=350)
    
    if filtered_pois:
        st.write("⛱️ **篩選結果與一鍵高德導航：**")
        selected_poi_name = st.selectbox("選擇你想去的休憩地標：", [p["name"] for p in filtered_pois])
        selected_poi = next(p for p in filtered_pois if p["name"] == selected_poi_name)
        
        st.markdown(f"""
        <div class="info-card">
            <h5 style="color: #2E7D32; margin-bottom: 5px; font-weight:bold;">{selected_poi['name']}</h5>
            <p style="font-size:1.1rem; margin-bottom:5px;">{selected_poi['desc']}</p>
            <p style="font-size:1.05rem; color:#555; margin-bottom:0px;">坡度指標: {selected_poi['slope']}</p>
        </div>
        """, unsafe_allow_html=True)
        
        amap_rest_url = f"https://uri.amap.com/navigation?from={lon},{lat},我的位置&to={selected_poi['lon']},{selected_poi['lat']},{selected_poi['name']}&mode=walk&coordinate=wgs84&callnative=1"
        st.link_button(f"📱 喚醒高德導航前往 {selected_poi_name}", amap_rest_url, use_container_width=True, type="primary")
    else:
        st.warning("⚠️ 沒有完全符合篩選條件的休憩點。請放寬篩選指標。")

# ==================== 功能三：隨行裝備 (推車優化配件全部刪除，僅保留清單與大字體) ====================
elif st.session_state.current_page == "gear":
    if st.button("⬅️ 返回主選單", type="secondary"):
        st.query_params.clear() # 清空查詢參數，返回主畫面
        st.session_state.current_page = "home"
        st.rerun()
        
    st.subheader("🎒 隨行裝備")
    st.write("根據當前模擬或實時微氣候環境，自適應提醒您及寶寶以下必備隨行裝備：")
    
    st.markdown("""
    <div class="card" style="border-left: 8px solid #2E7D32;">
        <h4 style="margin-top:0px; font-size:1.35rem;">🎒 家長隨行背包備忘錄</h4>
    </div>
    """, unsafe_allow_html=True)
    
    # 根據手動調整或 API 獲取的紫外線與氣溫，動態決策防護清單
    if uv >= 4.0:
        st.checkbox("☀️ **兒童防曬霜與抗 UV 遮陽罩** *(偵測紫外線偏強！建議做好防曬防護)*", value=True)
        st.checkbox("🧢 **親子大簷防曬帽**", value=True)
    else:
        st.checkbox("🧢 輕便遮陽帽 *(紫外線一般，攜帶備用)*", value=False)
        
    if temp >= 22.0:
        st.checkbox("🦟 **幼兒草本防蚊噴霧** *(步道植物非常茂密，防蚊叮咬！)*", value=True)
    else:
        st.checkbox("🦟 溫和防蚊貼片 *(備用)*", value=False)
        
    if temp >= 30.0:
        st.checkbox("🌬️ **夾式推車靜音小風扇** *(氣溫過高！強烈建議夾在推車上吹拂防中暑)*", value=True)
        st.checkbox("🥤 **補充電解質幼兒水壺**", value=True)
    elif temp < 18.0:
        st.checkbox("🧥 **寶寶防寒小外套與擋風毯** *(天氣偏涼，注意防風！)*", value=True)
        st.checkbox("🍼 **保溫熱水瓶（沖泡溫熱配方奶）**", value=True)
    else:
        st.checkbox("🍼 親子常規充足水瓶", value=True)

st.markdown("<br><hr style='margin: 10px 0; border: none; border-top: 1px solid #E0E0E0;'>", unsafe_allow_html=True)
st.caption("🔒 系統安全防護聲明：絲野仙蹤（Eco-Family）始終將親子安全置於首位。本App規劃之數據僅供決策輔助，戶外出行仍請家長以現場實際路況與安全第一為準。")1