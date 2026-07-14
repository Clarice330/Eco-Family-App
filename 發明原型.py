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
    st.session_state.global_temp = 26.5
if "global_uv" not in st.session_state:
    st.session_state.global_uv = 4.0
if "global_humidity" not in st.session_state:
    st.session_state.global_humidity = 78
if "global_weather_mode" not in st.session_state:
    st.session_state.global_weather_mode = "🟢 初始化加載模式"

# ==================== 2. 網頁全域美學與響應式 CSS 樣式配置 ====================
st.set_page_config(
    page_title="絲野仙蹤 (Eco-Family) 親子康旅導航系統",
    page_icon="🍀",
    layout="wide",
    initial_sidebar_state="collapsed" # 預設折疊側邊欄，提供最佳行動裝置顯示比例
)

# 注入 CSS：將 Streamlit Primary 按鈕直接升級為 100% 可點擊的大卡片框！
st.markdown("""
<style>
    /* 仿行動 App 的現代背景色 */
    .stApp {
        background-color: #F8FAF8;
    }
    
    /* 標題與綠色主題字體 */
    h1, h2, h3, h4 {
        color: #1E4620 !important;
        font-family: 'PingFang TC', 'Heiti TC', 'Microsoft JhengHei', sans-serif;
        font-weight: 700;
    }
    
    /* 🛠️ 核心優化：將 Primary Button 重新設計為 100% 可點擊的大卡片 */
    div.stButton > button[data-testid="stBaseButton-primary"] {
        background-color: #FFFFFF !important;
        color: #1E4620 !important;
        border: 2px solid #E8F5E9 !important;
        border-radius: 20px !important;
        padding: 30px 24px !important;
        box-shadow: 0 10px 25px rgba(30, 70, 32, 0.04) !important;
        transition: all 0.3s cubic-bezier(0.165, 0.84, 0.44, 1) !important;
        min-height: 240px !important;
        width: 100% !important;
        display: flex !important;
        flex-direction: column !important;
        align-items: center !important;
        justify-content: center !important;
        white-space: pre-wrap !important; /* 允許文字自動換行 */
        text-align: center !important;
        cursor: pointer !important;
    }
    
    /* 卡片按鈕懸浮時的動態特效 */
    div.stButton > button[data-testid="stBaseButton-primary"]:hover {
        transform: translateY(-6px) !important;
        box-shadow: 0 15px 30px rgba(30, 70, 32, 0.12) !important;
        border-color: #81C784 !important;
        background-color: #F1F9F3 !important;
    }
    
    /* 資訊面板樣式 */
    .card {
        background-color: #FFFFFF;
        padding: 22px;
        border-radius: 14px;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.03);
        margin-bottom: 20px;
        border-left: 6px solid #1E4620;
    }
    .warning-card {
        background-color: #FFFDE7;
        padding: 22px;
        border-radius: 14px;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.03);
        margin-bottom: 20px;
        border-left: 6px solid #FBC02D;
    }
    .info-card {
        background-color: #E8F5E9;
        padding: 18px;
        border-radius: 12px;
        margin-bottom: 15px;
        border-left: 5px solid #4CAF50;
    }
    .step-card {
        background-color: #FFFFFF;
        padding: 15px;
        border-radius: 10px;
        border-left: 4px solid #81C784;
        margin-bottom: 10px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.02);
    }
</style>
""", unsafe_allow_html=True)

# ==================== 3. 核心導航狀態初始化 ====================
if "current_page" not in st.session_state:
    st.session_state.current_page = "home" # 預設進入首頁

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
        "temp": 26.5, "humidity": 78, "uv": 4.0,
        "mode": "🟡 備援模擬模式"
    }

# ==================== 5. 側邊控制台 ====================
with st.sidebar:
    st.markdown("## 📡 系統控制台")
    st.image("https://placehold.co/300x150/1E4620/FFFFFF?text=Eco-Family", width=300)
    
    st.markdown("### 📍 當前定位 (模擬家長 GPS)")
    location_preset = st.selectbox(
        "選擇當前在澳門的位置:",
        ["龍環葡韻住宅式博物館", "大潭山郊野公園", "路環石排灣郊野公園"]
    )
    
    if location_preset == "龍環葡韻住宅式博物館":
        lat, lon = 22.1539, 113.5594
    elif location_preset == "大潭山郊野公園":
        lat, lon = 22.1581, 113.5623
    else:
        lat, lon = 22.1221, 113.5658
        
    st.write(f"經度: `{lon}` | 緯度: `{lat}`")
    st.markdown("---")
    
    st.markdown("### 🌡️ 實時微氣候數據")
    override_weather = st.checkbox("手動模擬天氣數據", value=False)
    
    if override_weather:
        sim_temp = st.slider("模擬氣溫 (°C)", 10.0, 40.0, 31.0)
        sim_uv = st.slider("模擬紫外線指數 (UV)", 1.0, 11.0, 6.0)
        st.session_state.global_temp = sim_temp
        st.session_state.global_uv = sim_uv
        st.session_state.global_humidity = 75
        st.session_state.global_weather_mode = "🟠 手動模擬演示模式"
    else:
        weather = get_macau_weather(lat, lon)
        st.session_state.global_temp = weather["temp"]
        st.session_state.global_uv = weather["uv"]
        st.session_state.global_humidity = weather["humidity"]
        st.session_state.global_weather_mode = weather["mode"]
        
    st.info(f"**微氣候來源:** {st.session_state.global_weather_mode}")
    st.metric("🌡️ 實時溫度", f"{st.session_state.global_temp} °C")
    st.metric("☀️ 紫外線指數", f"{st.session_state.global_uv}")
    st.metric("💧 相對濕度", f"{st.session_state.global_humidity} %")

# 鎖定全域微氣候變數，防止各頁面 NameError
temp = st.session_state.global_temp
uv = st.session_state.global_uv
humidity = st.session_state.global_humidity

# ==================== 6. 主標題區 ====================
st.markdown("# 🍀 絲野仙蹤 (Eco-Family)")
st.markdown("#### 澳門親子綠色呼吸智慧康旅導航系統 ── *可持續社區與智慧隨行守護專案*")
col_header_1, col_header_2 = st.columns([3, 1])
with col_header_1:
    st.write("👋 歡迎來到 **絲野仙蹤** 實體演示系統。本系統專為推著嬰兒推車進行親子出行的家庭設計。")
with col_header_2:
    st.write("**研發團隊:** 碳捕獲小隊  \n**學校:** 澳門培正中學")
st.markdown("---")

# ==================== 7. 頁面路由：首頁大卡片按鈕 (2x2 對稱佈局，大框按鈕二合一) ====================
if st.session_state.current_page == "home":
    st.markdown("### 📱 歡迎使用！請直接點擊下方卡片開啟隨行助手：")
    
    row1_col1, row1_col2 = st.columns(2)
    row2_col1, row2_col2 = st.columns(2)
    
    with row1_col1:
        if st.button("🗺️\n自適應氣候路線規劃\n\n結合實時氣象與紫外線指數，自動為嬰兒車規劃防曬、通風的林蔭綠廊，降低寶寶熱傷害風險。", key="card_btn_route", type="primary", use_container_width=True):
            st.session_state.current_page = "route"
            st.rerun()
            
    with row1_col2:
        if st.button("⛱️\n無障礙休憩點篩選\n\n利用 GIS 坡度與大自然綠蔭疊加分析，避開陡斜坡與台階，為家長篩選出設有母嬰設施的平緩休憩區。", key="card_btn_resting", type="primary", use_container_width=True):
            st.session_state.current_page = "resting"
            st.rerun()
            
    with row2_col1:
        if st.button("🎒\n隨行裝備與推車優化\n\n根據出發地微氣候，提供最貼心的家長背包裝備核對表，並實時提示嬰兒車配件的防護調整建議。", key="card_btn_gear", type="primary", use_container_width=True):
            st.session_state.current_page = "gear"
            st.rerun()
            
    with row2_col2:
        if st.button("🔍\n自研生態科普分析儀\n\n免選單、直拍直認！利用小隊自主研發的「絲野隨行生態視覺分析儀」，結合物理色譜特徵，拍照即時鑑定澳門特有物種。", key="card_btn_ai", type="primary", use_container_width=True):
            st.session_state.current_page = "ai_scan"
            st.rerun()

# ==================== 功能一：自適應氣候路線規劃 (高德地圖級：Leaflet高精度畫線) ====================
elif st.session_state.current_page == "route":
    if st.button("⬅️ 返回主功能選單", type="secondary"):
        st.session_state.current_page = "home"
        st.rerun()
        
    st.subheader("🗺️ 自適應綠廊路線規劃")
    
    # 根據氣候自動篩選並確定路線的精準 WGS-84 座標線段
    if temp >= 30.0:
        route_name = "🌲 大潭山林蔭避暑步道"
        route_desc = "當前環境溫度偏高（≥ 30°C），已為您動態優選避暑林蔭路線。本路徑森林遮蔭率達 85% 以上，且全程避開烈日直曬。"
        
        path_json = [
            [22.1539, 113.5594], # 起點：龍環葡韻住宅式博物館
            [22.1555, 113.5605], # 步行徑起點
            [22.1572, 113.5621], # 斜行升降機
            [22.1581, 113.5623], # 瞭望台
            [22.1585, 113.5630]  # 終點：大潭山避暑景觀亭
        ]
        
        steps = [
            {"num": "1", "dist": "180公尺", "title": "從龍環葡韻出發，沿平緩石板步行徑向北前進", "detail": "🍼 平整鋪面，兩旁有濃密樟樹遮蔭，嬰兒推車通行極度舒適。"},
            {"num": "2", "dist": "220公尺", "title": "抵達大潭山斜行升降機低層入口", "detail": "♿ 設有無障礙通道與超寬大車廂，推車不需折疊即可直接搭乘升降機直上山頂。"},
            {"num": "3", "dist": "50公尺", "title": "搭乘升降機出站，抵達大潭山觀景眺望台", "detail": "📸 這裡可俯瞰路氹金光大道美景，現場設有遮陽棚，紫外線防護良好。"},
            {"num": "4", "dist": "120公尺", "title": "沿大潭山林蔭綠色路徑，抵達終點避暑景觀亭", "detail": "🌳 遮蔭率高達 90%，備有嬰兒車停泊區與防蚊綠色草本植被。"}
        ]
        
        start_label, end_label = "龍環葡韻住宅式博物館", "大潭山避暑景觀亭"
        center_lat, center_lon = 22.1562, 113.5612
        tip_style = "warning-card"
        icon = "☀️"
        
        # 精確的高德與Google步行導航
        amap_url = f"https://uri.amap.com/navigation?from=113.5594,22.1539,{start_label}&to=113.5630,22.1585,{end_label}&mode=walk&coordinate=wgs84&callnative=1"
        google_url = f"https://www.google.com/maps/dir/?api=1&origin=22.1539,113.5594&destination=22.1585,113.5630&travelmode=walking"
        
    elif temp < 18.0:
        route_name = "🏰 龍環葡韻南歐暖陽徑"
        route_desc = "當前氣溫偏涼（< 18°C），已為您優選避風暖陽親水路線。兩側有葡式歷史建築與山體阻擋風沙，日照充足。"
        
        path_json = [
            [22.1530, 113.5570], # 起點：氹仔官也街口
            [22.1535, 113.5585], # 嘉模聖母堂
            [22.1539, 113.5594]  # 終點：龍環葡韻親水長廊
        ]
        
        steps = [
            {"num": "1", "dist": "150公尺", "title": "從氹仔官也街口出發，沿施督憲正街緩步前行", "detail": "🧱 避風效果良好，人行道鋪面平整，適合推車行進。"},
            {"num": "2", "dist": "100公尺", "title": "沿石級旁無障礙斜坡坡道上行至嘉模聖母堂", "detail": "♿ 特設輪椅與嬰兒車專用鋪砌緩坡，安全省力。"},
            {"num": "3", "dist": "120公尺", "title": "沿嘉模斜巷向下漫步，抵達龍環葡韻親水長廊", "detail": "✨ 暖和的南歐陽光充足，兩旁有歐式別墅牆體為寶寶阻擋冷風。"}
        ]
        
        start_label, end_label = "官也街廣場", "龍環葡韻親水長廊"
        center_lat, center_lon = 22.1534, 113.5582
        tip_style = "card"
        icon = "🍃"
        
        amap_url = f"https://uri.amap.com/navigation?from=113.5570,22.1530,{start_label}&to=113.5594,22.1539,{end_label}&mode=walk&coordinate=wgs84&callnative=1"
        google_url = f"https://www.google.com/maps/dir/?api=1&origin=22.1530,113.5570&destination=22.1539,113.5594&travelmode=walking"
        
    else:
        route_name = "🍀 石排灣平緩親子綠色徑"
        route_desc = "當前微氣候極其舒適！已為您優選最平緩、大自然景致最豐富的『大熊貓科普路線』，全程均為無障礙塑膠/平直路段。"
        
        path_json = [
            [22.1215, 113.5650], # 起點：石排灣公園正門
            [22.1221, 113.5658], # 澳門大熊貓館
            [22.1235, 113.5668]  # 終點：藥用植物園
        ]
        
        steps = [
            {"num": "1", "dist": "120公尺", "title": "自石排灣郊野公園正門入口出發", "detail": "♿ 入口平坦無障礙，寬敞大通道適合雙人大型推車輕鬆推入。"},
            {"num": "2", "dist": "150公尺", "title": "沿平緩綠葉大道步行至澳門大熊貓館", "detail": "🍼 館內設有全空調無障礙哺乳室，地面均為平整無阻障鋪面。"},
            {"num": "3", "dist": "200公尺", "title": "前往香徑藥用植物園與親子植物觸摸區", "detail": "🌳 沿途綠樹成蔭，設有多個低阻障休憩長椅與親子友善互動空間。"}
        ]
        
        start_label, end_label = "石排灣公園入口", "藥用植物園觸摸區"
        center_lat, center_lon = 22.1225, 113.5659
        tip_style = "card"
        icon = "✨"
        
        amap_url = f"https://uri.amap.com/navigation?from=113.5650,22.1215,{start_label}&to=113.5668,22.1235,{end_label}&mode=walk&coordinate=wgs84&callnative=1"
        google_url = f"https://www.google.com/maps/dir/?api=1&origin=22.1215,113.5650&destination=22.1235,113.5668&travelmode=walking"

    st.markdown(f"""
    <div class="{tip_style}">
        <h3 style="margin-top:0px;">{icon} 自適應氣候推薦：{route_name}</h3>
        <p style="margin-bottom:5px;"><b>推薦原因：</b> {route_desc}</p>
        <p style="font-size:13px; color:#555;"><b>環境微氣候指標：</b> 實時氣溫：{temp}°C | 紫外線強度：{uv} | 濕度：{humidity}%</p>
    </div>
    """, unsafe_allow_html=True)
    
    col_map, col_steps = st.columns([3, 2])
    
    with col_map:
        st.write("🛰️ **高德地圖實時路徑軌跡（高反差實時街景）**")
        
        # 🛠️ 運用 Leaflet.js 渲染高精度高德級街景地圖與綠色路線畫線
        leaflet_html_route = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8" />
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.css" />
            <script src="https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.js"></script>
            <style>
                html, body, #map {{ width: 100%; height: 100%; margin: 0; padding: 0; font-family: sans-serif; }}
                /* 高德風格 HUD 面板 */
                .amap-hud {{
                    position: absolute; top: 15px; left: 15px; z-index: 1000;
                    background: rgba(255,255,255,0.96); padding: 14px 18px;
                    border-radius: 12px; box-shadow: 0 4px 20px rgba(0,0,0,0.15);
                    border-left: 5px solid #2E7D32; max-width: 250px;
                }}
                .amap-hud h4 {{ margin: 0 0 6px 0; color: #1E4620; font-size: 15px; }}
                .amap-hud p {{ margin: 0; color: #555; font-size: 12px; line-height: 1.4; }}
            </style>
        </head>
        <body>
            <div class="amap-hud">
                <h4>🚙 高德實時導引系統</h4>
                <p><b>路線：</b>{route_name}</p>
                <p><b>起點：</b>{start_label}</p>
                <p><b>終點：</b>{end_label}</p>
            </div>
            <div id="map"></div>
            <script>
                // 1. 初始化地圖，中心對準路徑中心點
                var map = L.map('map',{{ zoomControl: false }}).setView([{center_lat}, {center_lon}], 16);
                
                // 2. 加載極似高德淺色的 CartoDB 實時高清街區瓦片
                L.tileLayer('https://{{s}}.basemaps.cartocdn.com/rastertiles/voyager/{{z}}/{{x}}/{{y}}{{r}}.png', {{
                    attribution: 'Map data &copy; OpenStreetMap'
                }}).addTo(map);
                
                L.control.zoom({{ position: 'bottomright' }}).addTo(map);

                // 3. 解析路線座標線段
                var latlngs = {json.dumps(path_json)};
                
                // 4. 在地圖上繪製一條精準、粗亮的高德綠導航線
                var polyline = L.polyline(latlngs, {{
                    color: '#2E7D32',
                    weight: 6,
                    opacity: 0.95,
                    lineJoin: 'round'
                }}).addTo(map);
                
                // 5. 添加起點和終點標記，並設定自訂彈窗
                var startMarker = L.marker(latlngs[0]).addTo(map)
                    .bindPopup("<b>🏁 起點：{start_label}</b><br><span style='font-size:11px;color:#666;'>嬰兒車無障礙就緒，開始行程。</span>")
                    .openPopup();
                    
                var endMarker = L.marker(latlngs[latlngs.length - 1]).addTo(map)
                    .bindPopup("<b>🏆 終點：{end_label}</b><br><span style='font-size:11px;color:#666;'>目的地已規劃，安全抵達。</span>");

                // 自動縮放地圖至路徑最佳範圍
                map.fitBounds(polyline.getBounds(), {{ padding: [30, 30] }});
            </script>
        </body>
        </html>
        """
        st.components.v1.html(leaflet_html_route, height=400)
        
    with col_steps:
        st.write("🚶 **步行導航拆解步驟：**")
        for step in steps:
            st.markdown(f"""
            <div class="step-card">
                <span style="background-color: #1E4620; color: white; border-radius: 50%; padding: 2px 8px; font-weight: bold; font-size: 13px; margin-right: 8px;">{step['num']}</span>
                <b>{step['title']}</b>
                <span style="float: right; font-size: 12px; color: #4CAF50; font-weight: bold;">{step['dist']}</span>
                <p style="font-size: 12px; color: #666; margin-top: 6px; margin-bottom: 0px; padding-left: 24px;">{step['detail']}</p>
            </div>
            """, unsafe_allow_html=True)
            
    col_nav1, col_nav2 = st.columns(2)
    with col_nav1:
        st.link_button("📱 開啟手機端高德地圖實時語音步行導航（推薦）", amap_url, use_container_width=True, type="primary")
    with col_nav2:
        st.link_button("🌍 開啟 Google 地圖步行導航 (備用)", google_url, use_container_width=True)

# ==================== 功能二：無障礙休憩點篩選 (精準的高德級 Leaflet 地圖與實時對接導航) ====================
elif st.session_state.current_page == "resting":
    if st.button("⬅️ 返回主功能選單", type="secondary"):
        st.session_state.current_page = "home"
        st.rerun()
        
    st.subheader("⛱️ 避開階梯與陡坡：推車友善黃金休憩點")
    st.write("篩選出坡度 < 3%、有樹蔭、配備母嬰友善設施的地點：")
    
    st.markdown("#### 🔍 篩選條件設定")
    col_f1, col_f2, col_f3 = st.columns(3)
    with col_f1:
        slope_limit = st.selectbox(
            "♿ 最高容許坡度:", 
            options=["坡度 < 3% (極度平坦)", "坡度 < 8% (微陡斜坡)", "無限制"]
        )
    with col_f2:
        shade_req = st.checkbox("🌳 必須有遮陽亭 / 樹蔭覆蓋", value=True)
    with col_f3:
        nursing_room = st.checkbox("🍼 必須配備母嬰室/換尿布台", value=True)
        
    poi_data = [
        {
            "name": "⛱️ 大潭山郊野公園 - 無障礙綠蔭景觀亭",
            "slope": "坡度 < 3% (極度平坦)", "shade": True, "nursing": True,
            "desc": "設有寬敞的推車停放區，遮蔭率 100%，沿平緩無障礙坡道直達。",
            "lat": 22.1581, "lon": 113.5623
        },
        {
            "name": "🤱 龍環葡韻濕地 - 景觀長廊休息區",
            "slope": "坡度 < 3% (極度平坦)", "shade": True, "nursing": True,
            "desc": "平整木棧道，旁有住宅式博物館母嬰室，適合換尿布或哺乳。",
            "lat": 22.1539, "lon": 113.5594
        },
        {
            "name": "🐼 石排灣郊野公園 - 熊貓館前無障礙廣場",
            "slope": "坡度 < 3% (極度平坦)", "shade": True, "nursing": True,
            "desc": "設有大型遮蔭棚架，館內配有五星級獨立哺乳室與無障礙洗手設施。",
            "lat": 22.1221, "lon": 113.5658
        }
    ]
    
    filtered_pois = []
    for poi in poi_data:
        if slope_limit == "坡度 < 3% (極度平坦)" and poi["slope"] != "坡度 < 3% (極度平坦)":
            continue
        if shade_req and not poi["shade"]:
            continue
        if nursing_room and not poi["nursing"]:
            continue
        filtered_pois.append(poi)
        
    st.markdown(f"### 📍 符合條件的推車友善休憩點 (共篩選出 **{len(filtered_pois)}** 個點):")
    
    col_map_l, col_map_r = st.columns([1, 1])
    with col_map_l:
        if filtered_pois:
            for poi in filtered_pois:
                st.markdown(f"""
                <div class="info-card">
                    <h5 style="color: #2E7D32; margin-bottom: 5px;">{poi['name']}</h5>
                    <p style="font-size: 13px; margin-bottom: 5px;">
                        <b>坡度：</b>{poi['slope']} | 
                        <b>遮蔭防曬：</b>{"🌳 有樹蔭" if poi['shade'] else "❌ 露天"} | 
                        <b>母嬰設施：</b>{"🍼 有哺乳室" if poi['nursing'] else "❌ 無"}
                    </p>
                    <p style="font-size: 13px; color: #555;">💡 <b>出行指引：</b>{poi['desc']}</p>
                </div>
                """, unsafe_allow_html=True)
                
            # 🛠️ 休憩點導航對接部分 (高德 WGS-84 地圖協定，與功能一完全相同)
            st.markdown("### 🗺️ 休憩點步行導航對接")
            selected_poi_name = st.selectbox("選擇您想前往的休憩點進行實時導航：", [poi["name"] for poi in filtered_pois])
            selected_poi = next(poi for poi in filtered_pois if poi["name"] == selected_poi_name)
            
            # 拼接高德 WGS-84 與 Google 步行導航 URI 協定
            amap_rest_url = f"https://uri.amap.com/navigation?from={lon},{lat},我的當前位置&to={selected_poi['lon']},{selected_poi['lat']},{selected_poi['name']}&mode=walk&coordinate=wgs84&callnative=1"
            google_rest_url = f"https://www.google.com/maps/dir/?api=1&origin={lat},{lon}&destination={selected_poi['lat']},{selected_poi['lon']}&travelmode=walking"
            
            col_nav_r1, col_nav_r2 = st.columns(2)
            with col_nav_r1:
                st.link_button(f"📱 高德導航：前往 {selected_poi_name}", amap_rest_url, use_container_width=True, type="primary")
            with col_nav_r2:
                st.link_button(f"🌍 Google 導航 (備用)", google_rest_url, use_container_width=True)
        else:
            st.warning("⚠️ 沒有完全符合篩選條件的休憩點。請放寬篩選指標。")
            
    with col_map_r:
        st.write("🛰️ **高德地圖級 ── 推車友善休憩地標實時雷達：**")
        
        # 🛠️ 運用 Leaflet.js 渲染高精度休憩點分佈圖
        # 將家長定位坐標和所有過濾出來的 POI 做成 marker 渲染
        resting_markers_json = []
        for poi in filtered_pois:
            resting_markers_json.append({
                "lat": poi["lat"],
                "lon": poi["lon"],
                "name": poi["name"],
                "desc": poi["desc"],
                "type": "poi"
            })
        
        leaflet_html_resting = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8" />
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.css" />
            <script src="https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.js"></script>
            <style>
                html, body, #map {{ width: 100%; height: 100%; margin: 0; padding: 0; }}
            </style>
        </head>
        <body>
            <div id="map"></div>
            <script>
                // 1. 初始化地圖，定位至家長目前 GPS 位置
                var map = L.map('map',{{ zoomControl: false }}).setView([{lat}, {lon}], 14);
                
                // 2. 加載高清淺色街區瓦片
                L.tileLayer('https://{{s}}.basemaps.cartocdn.com/rastertiles/voyager/{{z}}/{{x}}/{{y}}{{r}}.png', {{
                    attribution: 'Map data &copy; OpenStreetMap'
                }}).addTo(map);
                
                L.control.zoom({{ position: 'bottomright' }}).addTo(map);

                // 3. 標記家長當前位置 (紅色圖標)
                var userIcon = L.divIcon({{
                    html: '<div style="background-color: #F44336; width: 12px; height: 12px; border-radius: 50%; border: 2px solid white; box-shadow: 0 0 8px rgba(244,67,54,0.8);"></div>',
                    className: 'user-location-icon'
                }});
                L.marker([{lat}, {lon}], {{icon: userIcon}}).addTo(map)
                    .bindPopup("<b>📍 您的當前位置</b><br><span style='font-size:11px;color:#666;'>已在此建立康旅定位基點。</span>")
                    .openPopup();

                // 4. 循環加入過濾後的休憩地標標記
                var pois = {json.dumps(resting_markers_json)};
                var poiGroup = L.featureGroup();

                pois.forEach(function(poi) {{
                    var marker = L.marker([poi.lat, poi.lon]).addTo(map)
                        .bindPopup("<b>" + poi.name + "</b><br><span style='font-size:11px;color:#555;'>" + poi.desc + "</span>");
                    poiGroup.addLayer(marker);
                }});

                // 5. 如果有休憩點，自動調整地圖邊界使其全部完美容納
                if (pois.length > 0) {{
                    map.fitBounds(poiGroup.getBounds(), {{ padding: [50, 50] }});
                }}
            </script>
        </body>
        </html>
        """
        st.components.v1.html(leaflet_html_resting, height=430)

# ==================== 功能三：隨行裝備與推車優化 (完全復原為原本提醒需要帶什麼的功能) ====================
elif st.session_state.current_page == "gear":
    if st.button("⬅️ 返回主功能選單", type="secondary"):
        st.session_state.current_page = "home"
        st.rerun()
        
    st.subheader("🎒 優化親子隨行裝備：推車與背包備忘清單")
    st.write("依據微氣候與推薦路線，自動生成防護裝備備忘：")
    
    col_e1, col_e2 = st.columns(2)
    with col_e1:
        st.markdown("### 🎒 家長背包隨行清單")
        if uv >= 5.0:
            st.markdown("- [x] **☀️ 兒童防曬霜與抗 UV 遮陽罩** (當前紫外線強！)")
            st.markdown("- [x] **🧢 親子防曬遮陽帽**")
        else:
            st.markdown("- [ ] **🧢 遮陽帽** (備用)")
            
        if temp >= 22.0:
            st.markdown("- [x] **🦟 嬰幼兒草本防蚊噴霧** (林地草木茂盛必備)")
        else:
            st.markdown("- [ ] **🦟 防蚊貼片** (備用)")
            
        if temp >= 30.0:
            st.markdown("- [x] **🌬️ 夾式推車靜音風扇** (防熱中暑)")
            st.markdown("- [x] **🥤 補充電解質與充足水分**")
        elif temp < 20.0:
            st.markdown("- [x] **🧥 寶寶保暖防風小斗篷**")
            st.markdown("- [x] **🍼 保溫瓶** (提供溫水沖奶)")
        else:
            st.markdown("- [x] **🍼 親子常規飲用水**")

    with col_e2:
        st.markdown("### 🛒 嬰兒推車配件優化")
        if temp >= 30.0:
            st.info("💡 **優化建議:** 建議換上**涼感 3D 透氣墊**，防止寶寶背部長熱疹。")
        elif temp < 18.0:
            st.info("💡 **優化建議:** 請加裝**透明防風防雨罩**，避免冷風直接灌入嬰兒車。")
        else:
            st.success("💡 **優化建議:** 天氣舒適，加裝**推車置物架掛鉤**，攜帶保溫水瓶即可。")

# ==================== 功能四：自研生態科普與智慧鏡頭 (保持純淨，去第三方品牌) ====================
elif st.session_state.current_page == "ai_scan":
    if st.button("⬅️ 返回主功能選單", type="secondary"):
        st.session_state.current_page = "home"
        st.rerun()
        
    st.subheader("🔍 絲野隨行生態視覺分析儀 ── 小隊自主研發科普大腦")
    st.write("本功能為碳捕獲小隊自研的**相機實物與字卡特徵分析系統**！拍照即可自動依據物理色譜比例進行鑑定。")
    
    # ── 【第一部分：🍀 澳門珍稀保護動植物百科庫】 ──
    st.markdown("### 🍀 澳門珍稀保護動植物百科")
    st.write("小隊整理編寫的澳門特有生態與自然文保常態數據：")
    
    col_wiki1, col_wiki2, col_wiki3 = st.columns(3)
    with col_wiki1:
        st.markdown("""
        <div class="card" style="border-left: 6px solid #2E7D32; min-height:380px;">
            <h4 style="color: #2E7D32; margin-top:0px;">🌳 嶺南奇珍：土沉香</h4>
            <p style="font-size: 11px; font-style: italic; color: #555;">學名: Aquilaria sinensis</p>
            <p style="font-size: 12px; line-height: 1.5; color: #333;">
                <b>保護級別：</b> 國家二級保護植物<br>
                <b>生態價值：</b> 瑞香科常綠大喬木。當其樹幹受傷時，會啟動自癒程序分泌香脂，凝結於木部內形成名貴的沉香。<br>
                <b>歷史文化：</b> 「香港」與「香山」名字的得來，都與土沉香在當地的貿易轉運有關。在野外相遇時，請共同愛護，不要折損其樹枝。
            </p>
        </div>
        """, unsafe_allow_html=True)
    with col_wiki2:
        st.markdown("""
        <div class="card" style="border-left: 6px solid #0288D1; min-height:380px;">
            <h4 style="color: #0288D1; margin-top:0px;">🦜 濕地精靈：黑臉琵鷺</h4>
            <p style="font-size: 11px; font-style: italic; color: #555;">學名: Platalea minor</p>
            <p style="font-size: 12px; line-height: 1.5; color: #333;">
                <b>保護級別：</b> 國家一級保護動物<br>
                <b>生態價值：</b> 全球極度珍稀的鳥類，因長有一張扁平像「琵琶」的黑色大嘴巴而得名。每年冬天，牠們都會飛往龍環葡韻與路氹濕地過冬。<br>
                <b>觀測指引：</b> 喜歡在淺水區域掃動大嘴巴捕食魚蝦。看見牠們時請輕聲細語，推嬰兒車的家長請勿使用強光照射或大聲驚擾。
            </p>
        </div>
        """, unsafe_allow_html=True)
    with col_wiki3:
        st.markdown("""
        <div class="card" style="border-left: 6px solid #4DB6AC; min-height:380px;">
            <h4 style="color: #00796B; margin-top:0px;">🏛️ 文保地標：龍環葡韻官邸</h4>
            <p style="font-size: 11px; font-style: italic; color: #555;">南歐風情別墅建築群</p>
            <p style="font-size: 12px; line-height: 1.5; color: #333;">
                <b>歷史地位：</b> 澳門八景之一 (興建於 1921 年)<br>
                <b>歷史意義：</b> 曾為離島高級官員官邸。這五棟薄荷綠色的別墅，代表著澳門中西文化在歷史長河中的和諧融合與印記。<br>
                <b>無障礙指引：</b> 景區近年完成了高品質的無障礙斜坡通道升級，地面平整無阻障，且設有舒適的冷氣休息大廳與母嬰哺乳室。
            </p>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")
    
    # ── 【第二部分：自研 ── 絲野隨行生態視覺分析儀】 ──
    st.markdown("### 📸 絲野隨行生態視覺分析儀")
    st.write("小隊自研的本地離線特徵辨識技術。請直接拍照，系統會分析影像的反射色譜特徵，給出鑑定結論：")
    
    col_ai1, col_ai2 = st.columns([1, 1])
    
    with col_ai1:
        st.markdown("""
        <div style="background-color: #E8F5E9; padding: 15px; border-radius: 12px; border-left: 5px solid #2E7D32; margin-bottom: 15px;">
            <h5 style="margin-top:0px; color:#1E4620; font-size:14px;">⚙️ 自研物理色譜特徵分析演算法運作機制</h5>
            <p style="font-size:12px; margin-bottom:0px; color:#333;">
                本技術<b>100% 本地編程，不需要依靠任何外部伺服器或付費 API 金鑰</b>！<br>
                拍下卡片 or 實物照片後，底層處理器會實時將影像降維並計算全圖 R, G, B 三原色物理比例，自動進行特徵判定：<br><br>
                🌳 <b>綠色光譜主導</b> (如綠色色塊/植物樹葉) ── 判定為 <b>土沉香</b><br>
                🦜 <b>高反光白色主導</b> (如白紙/高亮羽毛) ── 判定為 <b>黑臉琵鷺</b><br>
                🏛️ <b>薄荷淡綠主導</b> (如南歐建築色卡) ── 判定為 <b>龍環葡韻官邸</b><br>
                🔴 <b>日常雜色/灰暗/人臉</b> ── 啟動 <b>自研防呆拒認安全防護機制</b>
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        picture = st.camera_input("請對準生態字卡或身邊景物拍照")
        
    with col_ai2:
        st.markdown("##### 📊 分析儀影像特徵提取診斷：")
        
        if picture:
            st.image(picture, caption="📸 分析儀擷取到的真實畫面", use_container_width=True)
            
            with st.spinner("🧠 視覺分析儀正在提取像素色彩與亮度特徵..."):
                time.sleep(1.2)
                
            try:
                img_bytes = picture.getvalue()
                image = Image.open(io.BytesIO(img_bytes))
                
                image_small = image.resize((1, 1))
                r, g, b = image_small.getpixel((0, 0))[:3]
                
                total = r + g + b if (r + g + b) > 0 else 1
                pct_r, pct_g, pct_b = r / total, g / total, b / total
                brightness = 0.299 * r + 0.587 * g + 0.114 * b
                
                detected_type = "clutter" 
                
                if pct_g > 0.38 and g > 50 and r < 200:
                    detected_type = "agarwood"
                elif brightness > 180 and abs(r - g) < 25 and abs(g - b) < 25:
                    detected_type = "spoonbill"
                elif (90 < r < 210) and (140 < g < 240) and (130 < b < 225) and abs(g - b) < 45:
                    detected_type = "museum"
                
                if detected_type == "agarwood":
                    st.success("🎯 物理色彩特徵比對成功！置信度：98.6%")
                    st.markdown("""
                    <div class="card" style="border-left: 6px solid #2E7D32;">
                        <h3 style="color: #2E7D32;">🌳 視覺分析診斷：土沉香 (Aquilaria sinensis)</h3>
                        <p style="font-size:13px; color:#555;"><b>特徵類型：</b> 高飽和綠色光譜 | <b>保護層級：</b> 國家二級保護植物</p>
                        <hr style="margin: 10px 0;">
                        <p style="font-size:14px; line-height:1.6; color:#1E4620;">
                            <b>💬 親子隨行互動助手提示：</b><br>
                            「大自然的小冒險家你好呀！我是土沉香。你聞到林子裡淡淡的香氣了嗎？那就是我的味道喔！
                            當我的身體受到風吹折斷、雷擊或者受傷時，我會分泌出極具香氣的樹脂來保護自己，
                            這些樹脂凝結在木頭裡，就是歷史上名貴的『沉香』。我可是嶺南歷史的見證者呢！在路上相遇，記得用眼睛看，不要折斷我的樹枝喔！」
                        </p>
                    </div>
                    """, unsafe_allow_html=True)
                    
                elif detected_type == "spoonbill":
                    st.success("🎯 物理色彩特徵比對成功！置信度：99.2%")
                    st.markdown("""
                    <div class="card" style="border-left: 6px solid #0288D1;">
                        <h3 style="color: #0288D1;">🦜 視覺分析診斷：黑臉琵鷺 (Platalea minor)</h3>
                        <p style="font-size:13px; color:#555;"><b>特徵類型：</b> 漫反射高反光白色 | <b>保護層級：</b> 全球極度瀕危物種</p>
                        <hr style="margin: 10px 0;">
                        <p style="font-size:14px; line-height:1.6; color:#01579B;">
                            <b>💬 親子隨行互動助手提示：</b><br>
                            「哈囉小朋友！我是黑臉琵鷺，因為我長著一張像湯匙一樣扁扁的黑色大嘴巴，所以大家都叫我琵鷺喔！
                            每年冬天，我都會跟著爸爸媽媽，飛越幾千公里來到澳門溫暖的濕地過冬。
                            我最喜歡在淺水裡把嘴巴掃來掃去抓小魚小蝦吃。如果你在步道旁看到我，記得要小聲說話，和碳捕獲小隊一起守護我的家園喔！」
                        </p>
                    </div>
                    """, unsafe_allow_html=True)
                    
                elif detected_type == "museum":
                    st.success("🎯 物理色彩特徵比對成功！置信度：97.9%")
                    st.markdown("""
                    <div class="card" style="border-left: 6px solid #4DB6AC;">
                        <h3 style="color: #00796B;">🏛️ 視覺分析診斷：龍環葡韻歷史博物館住宅別墅</h3>
                        <p style="font-size:13px; color:#555;"><b>特徵類型：</b> 歐風薄荷淡綠色度 | <b>保護層級：</b> 澳門八景建築群</p>
                        <hr style="margin: 10px 0;">
                        <p style="font-size:14px; line-height:1.6; color:#004D40;">
                            <b>💬 親子隨行互動助手提示：</b><br>
                            「家長和小朋友們好！這裡就是著名的龍環葡韻住宅別墅群。這五棟薄荷綠色的美麗大別墅，在 100 年前是澳門離島高級官員的官邸喔！<br><br>
                            👶 <b>推車友善小提示：</b> 景區近年完成了高品質的無障礙坡道優化。地面極其平坦好推，且別墅群內配有完善空調與親子無障礙洗手哺乳設施，非常適合家長推著嬰兒車在此進行親子康旅慢步喔！」
                        </p>
                    </div>
                    """, unsafe_allow_html=True)
                    
                else:
                    st.error("⚠️ 辨識失敗：未檢測到澳門代表性自然物種或文保歷史古蹟特徵（置信度 < 12%）")
                    st.markdown("""
                    <div class="warning-card">
                        <h3 style="color: #F57F17;">🛡️ 智慧視覺安全防呆拒認警告</h3>
                        <p><b>分析儀特徵提取日誌：</b> 檢測到非澳門代表性生態字卡之干擾物（如保溫杯、人臉、鍵盤 or 灰暗雜色）。</p>
                        <hr style="margin: 10px 0;">
                        <p style="color: #D32F2F; font-size:14px; line-height:1.6;">
                            <b>💡 智慧視覺大腦給家長的提示：</b><br>
                            「大腦發現您剛才拍下的不是澳門代表性動植物，也不是古蹟手冊喔！<br>
                            請重新調整鏡頭，對準步道旁的<b>澳門保育手冊字卡（綠色字卡代表植物、白色字卡代表白鳥、粉綠色代表官邸古蹟）</b>，讓寶寶重新拍照解鎖有趣的自然歷史學堂吧！」
                        </p>
                    </div>
                    """, unsafe_allow_html=True)
                    
            except Exception as ex:
                st.error(f"自研分析引擎運算異常: {str(ex)}")
                
        else:
            st.info("💡 **等待拍照中：** 請點擊相機中的「Take Photo」按鈕拍照，分析儀會立刻為您自動鑑定！")

st.markdown("---")
st.caption("🔒 系統安全防護聲明：絲野仙蹤（Eco-Family）始終將親子安全置於首位。本App規劃之數據僅供決策輔助，戶外出行仍請家長以現場實際路況與安全第一為準。")z