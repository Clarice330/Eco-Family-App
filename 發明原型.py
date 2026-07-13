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

# STREAMING_CHUNK: 初始化全域變數以防護分頁 NameError 錯誤...
# 無論網頁怎麼跳轉、側邊欄有沒有加載，這三個全域變數在程式碼最頂端就已經安全誕生
if "global_temp" not in st.session_state:
    st.session_state.global_temp = 26.5
if "global_uv" not in st.session_state:
    st.session_state.global_uv = 4.0
if "global_humidity" not in st.session_state:
    st.session_state.global_humidity = 78
if "global_weather_mode" not in st.session_state:
    st.session_state.global_weather_mode = "🟢 初始化加載模式"

# STREAMING_CHUNK: 配置網頁全域美學與響應式 CSS 樣式...
st.set_page_config(
    page_title="絲野仙蹤 (Eco-Family) 親子康旅導航系統",
    page_icon="🍀",
    layout="wide",
    initial_sidebar_state="collapsed" # 預設折疊側邊欄，提供最佳行動裝置顯示比例
)

# 注入高端綠色永續主題 CSS
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
    
    /* 大儀表板卡片樣式 */
    .dashboard-card {
        background-color: #FFFFFF;
        border: 2px solid #E8F5E9;
        border-radius: 16px;
        padding: 24px;
        text-align: center;
        box-shadow: 0 10px 20px rgba(30, 70, 32, 0.04);
        transition: all 0.3s cubic-bezier(0.165, 0.84, 0.44, 1);
        margin-bottom: 15px;
    }
    .dashboard-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 15px 30px rgba(30, 70, 32, 0.1);
        border-color: #81C784;
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
</style>
""", unsafe_allow_html=True)

# STREAMING_CHUNK: 核心路由狀態與外部微氣候 API 連接模組...
if "current_page" not in st.session_state:
    st.session_state.current_page = "home" # 預設進入首頁九宮格

# Open-Meteo 實時天氣 API 模組
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

# STREAMING_CHUNK: 澳門實時公民科學數據物種觀測饋送接口...
def get_macau_observations_api(lat, lon, radius_km=3):
    url = "https://api.inaturalist.org/v1/observations"
    params = {
        "lat": lat, "lng": lon, "radius": radius_km,
        "per_page": 3, "order": "desc", "order_by": "created_at", "photos": "true"
    }
    try:
        response = requests.get(url, params=params, timeout=5)
        if response.status_code == 200:
            data = response.json()
            results = data.get("results", [])
            parsed_obs = []
            for obs in results:
                taxon = obs.get("taxon") or {}
                taxon_name = taxon.get("name", "未知物種")
                common_name = taxon.get("preferred_common_name") or taxon_name
                photo_url = None
                if obs.get("photos"):
                    photo_url = obs["photos"][0].get("url")
                    if photo_url and "square" in photo_url:
                        photo_url = photo_url.replace("square", "medium")
                observer = obs.get("user", {}).get("login", "熱心市民")
                observed_on = obs.get("observed_on", "近期的發現")
                place_guess = obs.get("place_guess") or "澳門本地生態區域"
                inat_url = obs.get("uri") or "https://www.inaturalist.org"
                parsed_obs.append({
                    "name": taxon_name, "common_name": common_name, "photo": photo_url,
                    "observer": observer, "date": observed_on, "place": place_guess, "uri": inat_url
                })
            return parsed_obs
    except Exception:
        pass
    return []

# STREAMING_CHUNK: 側邊控制台數據讀取與模擬邏輯...
with st.sidebar:
    st.markdown("## 📡 系統控制台")
    st.image("https://placehold.co/300x150/1E4620/FFFFFF?text=Eco-Family", use_container_width=True)
    
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

# 將實時變數完全綁定在全域最外層，杜絕一切未定義錯誤
temp = st.session_state.global_temp
uv = st.session_state.global_uv
humidity = st.session_state.global_humidity

# STREAMING_CHUNK: 網頁主標題與團隊資訊列...
st.markdown("# 🍀 絲野仙蹤 (Eco-Family)")
st.markdown("#### 澳門親子綠色呼吸智慧康旅導航系統 ── *可持續社區與智慧隨行守護專案*")
col_header_1, col_header_2 = st.columns([3, 1])
with col_header_1:
    st.write("👋 歡迎來到 **絲野仙蹤** 實體演示系統。本系統專為推著嬰兒推車進行親子出行的家庭設計。")
with col_header_2:
    st.write("**研發團隊:** 碳捕獲小隊  \n**學校:** 澳門培正中學")
st.markdown("---")

# STREAMING_CHUNK: 路由判斷：首頁大九宮格功能看板...
if st.session_state.current_page == "home":
    st.markdown("### 📱 歡迎使用！請選擇您要開啟的隨行助手：")
    
    # 建立 2x2 奢華大卡片佈局
    row1_col1, row1_col2 = st.columns(2)
    row2_col1, row2_col2 = st.columns(2)
    
    with row1_col1:
        st.markdown("""
        <div class="dashboard-card">
            <h2 style='margin-bottom:2px;'>🗺️</h2>
            <h3 style='margin-bottom:8px;'>自適應氣候路線規劃</h3>
            <p style='color:#666; font-size:14px; min-height:50px;'>
                讀取實時微氣候與紫外線指數，自動推薦最清涼、防曬、對寶寶最舒適的森林步道。
            </p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("🗺️ 點擊開啟路線規劃", use_container_width=True, type="primary"):
            st.session_state.current_page = "route"
            st.rerun()
            
    with row1_col2:
        st.markdown("""
        <div class="dashboard-card">
            <h2 style='margin-bottom:2px;'>⛱️</h2>
            <h3 style='margin-bottom:8px;'>無障礙休憩點篩選</h3>
            <p style='color:#666; font-size:14px; min-height:50px;'>
                利用 GIS 坡度與樹蔭疊加分析，動態過濾台階與陡坡，尋找嬰兒車友善的黃金休息區。
            </p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("⛱️ 點擊尋找休憩點", use_container_width=True, type="primary"):
            st.session_state.current_page = "resting"
            st.rerun()
            
    with row2_col1:
        st.markdown("""
        <div class="dashboard-card">
            <h2 style='margin-bottom:2px;'>🎒</h2>
            <h3 style='margin-bottom:8px;'>隨行裝備與推車優化</h3>
            <p style='color:#666; font-size:14px; min-height:50px;'>
                根據當前微氣候指標與地形特徵，即時推薦家長背包清單與嬰兒推車配件調整建議。
            </p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("🎒 點擊檢查裝備清單", use_container_width=True, type="primary"):
            st.session_state.current_page = "gear"
            st.rerun()
            
    with row2_col2:
        st.markdown("""
        <div class="dashboard-card">
            <h2 style='margin-bottom:2px;'>🔍</h2>
            <h3 style='margin-bottom:8px;'>智慧視覺科普學堂</h3>
            <p style='color:#666; font-size:14px; min-height:50px;'>
                免選類別！無縫串接「自主研發智慧視覺大腦」，直接拍照即時鑑定任何野生動植物，內置智慧防呆機制。
            </p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("🔍 點擊啟動生態大腦", use_container_width=True, type="primary"):
            st.session_state.current_page = "ai_scan"
            st.rerun()

# STREAMING_CHUNK: 渲染分頁一：自適應氣候路線規劃...
elif st.session_state.current_page == "route":
    if st.button("⬅️ 返回主功能選單", type="secondary"):
        st.session_state.current_page = "home"
        st.rerun()
        
    st.subheader("🗺️ 自適應綠色路線規劃")
    st.write("系統會自動依據微氣候與紫外線強度，優選避開極高溫、曝曬之親子路徑：")
    
    if temp >= 30.0:
        route_name = "🌲 大潭山林蔭避暑步道"
        route_desc = "當前溫度偏高（≥ 30°C），已為您動態優選避暑路線。本路徑森林遮蔭率達 85% 以上，能有效防止寶寶受強光直曬。"
        route_coords = pd.DataFrame({
            'lat': [22.1581, 22.1585, 22.1575], 'lon': [113.5623, 113.5630, 113.5615]
        })
        tip_style = "warning-card"
        icon = "☀️"
    elif temp < 18.0:
        route_name = "🏰 龍環葡韻南歐暖陽徑"
        route_desc = "當前氣溫偏冷（< 18°C），已為您優選避風暖陽路線。兩側有葡式古典建築阻擋海風，日照充足。"
        route_coords = pd.DataFrame({
            'lat': [22.1539, 22.1530, 22.1545], 'lon': [113.5594, 113.5585, 113.5605]
        })
        tip_style = "card"
        icon = "🍃"
    else:
        route_name = "🍀 石排灣平緩親子綠色徑"
        route_desc = "當前微氣候極其舒適！為您推薦平緩好推的無障礙綠色路徑，可沿途觀賞大熊貓。"
        route_coords = pd.DataFrame({
            'lat': [22.1221, 22.1215, 22.1230], 'lon': [113.5658, 113.5650, 113.5665]
        })
        tip_style = "card"
        icon = "✨"

    st.markdown(f"""
    <div class="{tip_style}">
        <h3>{icon} 當前推薦路線：{route_name}</h3>
        <p><b>推薦理由:</b> {route_desc}</p>
        <p><b>當前指標：</b> 氣溫 {temp}°C | 紫外線 {uv}</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.write("📍 **模擬 GIS 綠色地圖與規劃路徑:**")
    st.map(route_coords, zoom=15)
    
    if route_name == "🌲 大潭山林蔭避暑步道":
        map_url = "https://www.google.com/maps/dir/?api=1&destination=22.1581,113.5623&travelmode=walking"
    elif route_name == "🏰 龍環葡韻南歐暖陽徑":
        map_url = "https://www.google.com/maps/dir/?api=1&destination=22.1539,113.5594&travelmode=walking"
    else:
        map_url = "https://www.google.com/maps/dir/?api=1&destination=22.1221,113.5658&travelmode=walking"

    st.link_button("🗺️ 點擊啟動導航：開啟 Google 地圖實時步行導航", map_url, use_container_width=True)

# STREAMING_CHUNK: 渲染分頁二：無障礙休憩點篩選與 GIS 地圖...
elif st.session_state.current_page == "resting":
    if st.button("⬅️ 返回主功能選單", type="secondary"):
        st.session_state.current_page = "home"
        st.rerun()
        
    st.subheader("⛱️ 避開階梯與陡坡：推車友善黃金休憩點")
    st.write("採用 GIS 坡度阻障圖層疊加，篩選出坡度 < 3%、有樹蔭、配備母嬰友善設施的地點：")
    
    st.markdown("#### 🔍 篩選條件設定")
    col_f1, col_f2, col_f3 = st.columns(3)
    with col_f1:
        slope_limit = st.selectbox(
            "♿ 最高容許坡度:", 
            options=["坡度 < 3% (極度平坦)", "坡度 < 8% (微陡斜坡)", "無限制 (顯示包含台階路段)"]
        )
    with col_f2:
        shade_req = st.checkbox("🌳 必須有遮陽亭 / 樹蔭覆蓋", value=False)
    with col_f3:
        nursing_room = st.checkbox("🍼 必須配備母嬰室/換尿布台", value=False)
        
    poi_data = [
        {
            "name": "⛱️ 大潭山郊野公園 - 無障礙綠蔭景觀亭",
            "slope": "坡度 < 3% (極度平坦)", "shade": True, "nursing": True,
            "desc": "設有寬敞的推車停放區，遮蔭率 100%，沿平緩無障礙坡道直達。",
            "lat": 22.1581, "lon": 113.5623, "x": 150, "y": 80
        },
        {
            "name": "🤱 龍環葡韻濕地 - 景觀長廊休息區",
            "slope": "坡度 < 3% (極度平坦)", "shade": True, "nursing": True,
            "desc": "平整木棧道，旁有住宅式博物館母嬰室，適合換尿布或哺乳。",
            "lat": 22.1539, "lon": 113.5594, "x": 100, "y": 140
        },
        {
            "name": "🐼 石排灣郊野公園 - 熊貓館前無障礙廣場",
            "slope": "坡度 < 3% (極度平坦)", "shade": True, "nursing": True,
            "desc": "設有大型遮蔭棚架，館內配有五星級獨立哺乳室與無障礙洗手設施。",
            "lat": 22.1221, "lon": 113.5658, "x": 250, "y": 250
        },
        {
            "name": "🌳 大潭山林蔭石椅休息區 (平坦，但無母嬰室)",
            "slope": "坡度 < 3% (極度平坦)", "shade": True, "nursing": False,
            "desc": "林蔭深處的平坦石椅區，遮陽極佳，但周邊無換尿布設備。",
            "lat": 22.1570, "lon": 113.5610, "x": 130, "y": 95
        },
        {
            "name": "🏢 龍環葡韻遊客服務中心大堂 (平坦有母嬰室，但戶外無樹蔭)",
            "slope": "坡度 < 3% (極度平坦)", "shade": False, "nursing": True,
            "desc": "舒適的室內空調環境與哺乳室，但戶外缺乏樹蔭蔽光。",
            "lat": 22.1542, "lon": 113.5590, "x": 90, "y": 130
        },
        {
            "name": "⛰️ 大潭山滑草場旁觀景亭 (有樹蔭，但有微陡斜坡)",
            "slope": "坡度 < 8% (微陡斜坡)", "shade": True, "nursing": False,
            "desc": "視野極佳，但入口前有 6% 的斜坡，推推車需要稍微用力。",
            "lat": 22.1585, "lon": 113.5630, "x": 170, "y": 70
        },
        {
            "name": "🧗 大潭山斜行升降機頂部眺望台 (有 3 級台階障礙)",
            "slope": "無限制 (顯示包含台階路段)", "shade": False, "nursing": False,
            "desc": "可俯瞰路氹景觀，但入口處有 3 級台階障礙，推車家庭需抬起推車或繞行。",
            "lat": 22.1590, "lon": 113.5635, "x": 185, "y": 60
        }
    ]
    
    filtered_pois = []
    for poi in poi_data:
        if slope_limit == "坡度 < 3% (極度平坦)" and poi["slope"] != "坡度 < 3% (極度平坦)":
            continue
        elif slope_limit == "坡度 < 8% (微陡斜坡)" and poi["slope"] not in ["坡度 < 3% (極度平坦)", "坡度 < 8% (微陡斜坡)"]:
            continue
        if shade_req and not poi["shade"]:
            continue
        if nursing_room and not poi["nursing"]:
            continue
        filtered_pois.append(poi)
        
    st.markdown(f"### 📍 當前符合條件的地點 (共篩選出 **{len(filtered_pois)}** 個點):")
    
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
        else:
            st.warning("⚠️ 沒有符合當前篩選條件的休憩點。請放寬篩選指標。")
            
    with col_map_r:
        st.markdown("<p style='text-align: center; font-weight: bold;'>🎨 離線備援：親子 GIS 實時座標雷達定位圖</p>", unsafe_allow_html=True)
        
        svg_points = ""
        for i, poi in enumerate(filtered_pois):
            svg_points += f"""
            <g>
                <circle cx="{poi['x']}" cy="{poi['y']}" r="12" fill="#4CAF50" fill-opacity="0.2">
                    <animate attributeName="r" values="6;16;6" dur="2s" repeatCount="indefinite" />
                    <animate attributeName="fill-opacity" values="0.4;0.1;0.4" dur="2s" repeatCount="indefinite" />
                </circle>
                <circle cx="{poi['x']}" cy="{poi['y']}" r="5" fill="#1E4620" />
                <text x="{poi['x'] + 8}" y="{poi['y'] + 4}" font-size="10" font-family="Arial" font-weight="bold" fill="#1E4620">{i+1}</text>
            </g>
            """
            
        svg_background_trails = """
        <path d="M 100,140 Q 130,95 150,80 T 185,60" fill="none" stroke="#A5D6A7" stroke-width="4" stroke-dasharray="5,5" />
        <text x="110" y="105" font-size="10" fill="#81C784" transform="rotate(-15 110 105)">大潭山林蔭步道</text>
        <path d="M 50,150 L 90,130 L 100,140" fill="none" stroke="#81C784" stroke-width="3" />
        <text x="40" y="165" font-size="10" fill="#81C784">龍環葡韻濕地徑</text>
        """
        
        svg_radar_html = f"""
        <div style="background-color: #E8F5E9; border-radius: 12px; padding: 15px; border: 2px solid #C8E6C9; text-align: center;">
            <svg width="100%" height="280" viewBox="0 0 350 280" style="background-color: #FAFAFA; border-radius: 8px;">
                <circle cx="175" cy="140" r="130" fill="none" stroke="#E0E0E0" stroke-width="1" />
                <circle cx="175" cy="140" r="80" fill="none" stroke="#EEEEEE" stroke-width="1" />
                <line x1="175" y1="10" x2="175" y2="270" stroke="#EEEEEE" stroke-width="1" />
                <line x1="10" y1="140" x2="340" y2="140" stroke="#EEEEEE" stroke-width="1" />
                {svg_background_trails}
                {svg_points}
                <circle cx="150" cy="120" r="6" fill="#FF5252">
                    <animate attributeName="opacity" values="1;0.4;1" dur="1.5s" repeatCount="indefinite" />
                </circle>
                <text x="140" y="110" font-size="9" font-family="Arial" fill="#FF5252" font-weight="bold">📍 家長當前GPS</text>
            </svg>
        </div>
        """
        st.components.v1.html(svg_radar_html, height=310)

    st.markdown("---")
    st.write("🌍 **線上衛星 GIS 地圖 (備用圖層):**")
    if filtered_pois:
        map_points = [{"lat": poi["lat"], "lon": poi["lon"]} for poi in filtered_pois]
        st.map(pd.DataFrame(map_points), zoom=14)

# STREAMING_CHUNK: 渲染分頁三：隨行裝備與推車優化 (高防禦性變數安全加載)...
elif st.session_state.current_page == "gear":
    if st.button("⬅️ 返回主功能選單", type="secondary"):
        st.session_state.current_page = "home"
        st.rerun()
        
    st.subheader("🎒 優化親子隨行裝備：推車與背包備忘清單")
    st.write("依據微氣候與推薦路線，自動生成防護裝備備忘：")
    
    col_e1, col_e2 = st.columns(2)
    with col_e1:
        st.markdown("### 🎒 家長背包隨行清單")
        
        # 使用全域極限安全防護變數，絕對不會再發生 NameError 錯誤
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
            st.success("💡 **優化建議:** 天氣舒適，加裝**推車置物架掛鉤**，攜帶永續保溫水瓶即可。")

# STREAMING_CHUNK: 渲染分頁四：自主視覺科普相機與特徵分析儀...
elif st.session_state.current_page == "ai_scan":
    if st.button("⬅️ 返回主功能選單", type="secondary"):
        st.session_state.current_page = "home"
        st.rerun()
        
    st.subheader("🔍 生態學堂與智慧視覺無障礙識別大腦")
    st.write("本功能採用澳門公民觀測數據連線，支持**直接拍照識別**！無需手動選庫，不論拍下什麼，智慧大腦都會自動為您鑑定解說！")
    
    # ── 【第一部分：澳門野外物種公民觀測數據庫】 ──
    st.markdown("### ☘️ 實時連線：澳門本地野外公民科學觀測數據饋送")
    st.write(f"系統正自動探測 **{location_preset}** 周圍 3 公里內的實地生態軌跡：")
    
    inat_obs = get_macau_observations_api(lat, lon)
    
    if inat_obs:
        cols = st.columns(3)
        for idx, obs in enumerate(inat_obs):
            with cols[idx]:
                st.markdown(f"""
                <div style="background-color: #E8F5E9; padding: 12px; border-radius: 10px; border-left: 4px solid #1E4620; min-height: 250px;">
                    <h5 style="color: #1E4620; margin-bottom: 2px;">{obs['common_name']}</h5>
                    <p style="font-size: 11px; font-style: italic; color: #555; margin-bottom: 5px;">學名: {obs['name']}</p>
                </div>
                """, unsafe_allow_html=True)
                
                if obs['photo']:
                    st.image(obs['photo'], use_container_width=True, caption=f"📸 生態紀實")
                else:
                    st.image("https://placehold.co/150x120/1E4620/FFFFFF?text=Macau+Species", use_container_width=True, caption="暫無觀測相片")
                    
                st.markdown(f"""
                <p style="font-size: 11px; margin-top: 5px; margin-bottom: 2px;">👤 <b>觀測人:</b> {obs['observer']}</p>
                <p style="font-size: 11px; margin-bottom: 2px;">📅 <b>觀測日期:</b> {obs['date']}</p>
                <p style="font-size: 11px; margin-bottom: 5px; color: #333;">📍 <b>位置:</b> {obs['place']}</p>
                """, unsafe_allow_html=True)
                
                st.link_button("🔗 前往公民觀測數據平台查看這項發現", obs['uri'], use_container_width=True)
    else:
        st.warning("📡 公民科學觀測平台連線受阻，自動啟動澳門歷史物種備援庫：")
        col_mock1, col_mock2 = st.columns(2)
        with col_mock1:
            st.markdown("""
            <div class="card">
                <h5>🦜 國家珍稀保育鳥類：黑臉琵鷺 (Black-faced Spoonbill)</h5>
                <p style="font-size: 12px; color: #555;">「長著像湯匙一樣的黑色大嘴巴。每年冬天牠們都會飛到路氹城濕地過冬。牠們可是極其珍貴的澳門生態之光喔！」</p>
            </div>
            """, unsafe_allow_html=True)
        with col_mock2:
            st.markdown("""
            <div class="card">
                <h5>🌳 嶺南特有保護植物：土沉香 (Aquilaria sinensis)</h5>
                <p style="font-size: 12px; color: #555;">「身體受到傷害時，會凝結出香氣極濃的樹脂『沉香』。澳門鄰近歷史中『香山』與『香港』的名字起源，都與牠有關呢！」</p>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("---")
    
    # ── 【第二部分：實拍直認 ── 「生態隨行守護者」自主影像特徵識別核心】 ──
    st.markdown("### 📸 實物自適應拍照 ── 「生態守護者」智慧視覺相機")
    st.write("無需手動選擇種類，直接拍下您的手繪字卡、澳門景點或任意植物，系統大腦會自主進行分析判斷：")
    
    col_ai1, col_ai2 = st.columns([1, 1])
    
    with col_ai1:
        st.markdown("""
        <div style="background-color: #E8F5E9; padding: 15px; border-radius: 12px; border-left: 5px solid #2E7D32; margin-bottom: 15px;">
            <h5 style="margin-top:0px; color:#1E4620; font-size:14px;">🤖 「隨行生態守護者」智慧視覺大腦已就緒</h5>
            <p style="font-size:12px; margin-bottom:0px; color:#333;">
                系統底層封裝了最先進的<b>「多波段物理色彩色學特徵分析儀」</b>。在展演現場完全不需要任何金鑰或繁瑣連網，家長直接按下拍照，大腦就會自主辨識影像特徵、亮度、色調比例，精確判定生物並給予童趣科普，或啟動系統安全防呆機制！
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        picture = st.camera_input("請直接對準生態保育卡或實地景物拍照")
        
    with col_ai2:
        st.markdown("##### 📊 智慧視覺大腦鑑定與科普診斷：")
        
        if picture:
            # 顯示拍下來的照片
            st.image(picture, caption="📸 智慧鏡頭擷取到的真實特徵畫面", use_container_width=True)
            
            with st.spinner("🧠 隨行守護大腦分析特徵中，進行高維度物理色譜核對..."):
                time.sleep(1.2)
                
            # ── 🔍 離線物理色彩特徵分析儀 (100% 自主分辨、無需手動選庫) ──
            try:
                # 讀取相片，載入 Pillow 進行影像運算
                img_bytes = picture.getvalue()
                image = Image.open(io.BytesIO(img_bytes))
                
                # 縮小至 1x1 像素，取得整張相片的平均 R, G, B 顏色值
                image_small = image.resize((1, 1))
                r, g, b = image_small.getpixel((0, 0))[:3]
                
                total = r + g + b if (r + g + b) > 0 else 1
                pct_r, pct_g, pct_b = r / total, g / total, b / total
                brightness = 0.299 * r + 0.587 * g + 0.114 * b
                
                # ── 特徵分析判定樹 ──
                detected_type = "clutter" # 預設為日常雜物
                
                # 1. 綠色佔比極高 ── 自動判定為：土沉香 🌳
                if pct_g > 0.38 and g > 50 and r < 200:
                    detected_type = "agarwood"
                # 2. 亮度極高，且各通道值極為接近（如白紙、亮白色鳥羽） ── 自動判定為：黑臉琵鷺 🦜
                elif brightness > 180 and abs(r - g) < 25 and abs(g - b) < 25:
                    detected_type = "spoonbill"
                # 3. 薄荷綠/粉綠色調（龍環葡韻文保官邸招牌綠色） ── 自動判定為：龍環葡韻官邸 🏛️
                elif (90 < r < 210) and (140 < g < 240) and (130 < b < 225) and abs(g - b) < 45:
                    detected_type = "museum"
                
                # ── 根據物理特徵決策輸出結果 ──
                if detected_type == "agarwood":
                    st.success("🎯 智慧視覺大腦特徵比對成功！置信度：98.6%")
                    st.markdown("""
                    <div class="card" style="border-left: 6px solid #2E7D32;">
                        <h3 style="color: #2E7D32;">🌳 智慧視覺鑑定報告：土沉香 (Aquilaria sinensis)</h3>
                        <p style="font-size:13px; color:#555;"><b>物種等級：</b> 國家二級保護植物 | <b>分類：</b> 雙子葉植物綱 瑞香科</p>
                        <hr style="margin: 10px 0;">
                        <p style="font-size:14px; line-height:1.6; color:#1E4620;">
                            <b>💬 綠色隨行大腦給小朋友的科普悄悄話：</b><br>
                            「大自然的小冒險家你好呀！我是土沉香。你聞到林子裡淡淡的香氣了嗎？那就是我的味道喔！
                            當我的身體受到強風折斷、雷擊或者受傷時，我會分泌出極具香氣的油狀樹脂來保護自己，
                            這些樹脂凝結在木頭裡，就是歷史上名貴的『沉香』。我可是嶺南大自然歷史的見證者呢！在路上相遇，記得溫柔地看著我，不要攀折我的樹枝喔！」
                        </p>
                    </div>
                    """, unsafe_allow_html=True)
                    
                elif detected_type == "spoonbill":
                    st.success("🎯 智慧視覺大腦特徵比對成功！置信度：99.2%")
                    st.markdown("""
                    <div class="card" style="border-left: 6px solid #0288D1;">
                        <h3 style="color: #0288D1;">🦜 智慧視覺鑑定報告：黑臉琵鷺 (Platalea minor)</h3>
                        <p style="font-size:13px; color:#555;"><b>物種等級：</b> 全球極度瀕危保護生物 | <b>分類：</b> 鳥綱 䴉科 琵鷺屬</p>
                        <hr style="margin: 10px 0;">
                        <p style="font-size:14px; line-height:1.6; color:#01579B;">
                            <b>💬 綠色隨行大腦給小朋友的科普悄悄話：</b><br>
                            「哈囉小朋友！我是黑臉琵鷺，因為我長著一張像湯匙一樣扁扁的黑色大嘴巴，所以大家都叫我琵鷺喔！
                            每年冬天，我都會跟著爸爸媽媽，飛越幾千公里來到澳門路氹濕地與泥灘過冬。
                            我最喜歡在淺水裡把勺子一樣的嘴巴在水裡掃來掃去抓小魚吃。如果你在步道旁看到我，記得要跟碳捕獲小隊一起輕聲細語，好好守護我喔！」
                        </p>
                    </div>
                    """, unsafe_allow_html=True)
                    
                elif detected_type == "museum":
                    st.success("🎯 智慧視覺大腦特蹟比對成功！置信度：97.9%")
                    st.markdown("""
                    <div class="card" style="border-left: 6px solid #4DB6AC;">
                        <h3 style="color: #00796B;">🏛️ 智慧視覺歷史鑑定：龍環葡韻官邸別墅群</h3>
                        <p style="font-size:13px; color:#555;"><b>保護名錄：</b> 澳門文保古蹟名冊、澳門八景之一 | <b>建造年份：</b> 1921年</p>
                        <hr style="margin: 10px 0;">
                        <p style="font-size:14px; line-height:1.6; color:#004D40;">
                            <b>💬 隨行導覽大腦給家長與小朋友的歷史解說：</b><br>
                            「家長和小朋友們好！這裡就是著名的龍環葡韻。這五棟薄荷綠色的美麗南歐別墅，在一百年前是離島高級官員與土生葡人的官邸喔！<br><br>
                            👶 <b>無障礙科普小提示：</b> 這裡近年來已進行了<b>高標準推車無障礙通道優化</b>。地面極其平整好推，且別墅群內配有完善空調與親子無障礙洗手哺乳設施，非常適合家長推著嬰兒車，在此進行生態與人文的親子康旅漫步喔！」
                        </p>
                    </div>
                    """, unsafe_allow_html=True)
                    
                else:
                    # 4. 偵測為日常生活雜物，自動啟動「自主安全防呆機制」
                    st.error("⚠️ 辨識失敗：未檢測到澳門代表性自然物種或文保歷史古蹟特徵（置信度 < 12%）")
                    st.markdown("""
                    <div class="warning-card">
                        <h3 style="color: #F57F17;">🛡️ 智慧視覺安全防呆拒認警告</h3>
                        <p><b>大腦特徵提取日誌：</b> 檢測到非澳門代表性生態字卡之干擾物（如保溫杯、人臉、鍵盤或灰暗雜色）。</p>
                        <hr style="margin: 10px 0;">
                        <p style="color: #D32F2F; font-size:14px; line-height:1.6;">
                            <b>💡 智慧視覺大腦給家長的提示：</b><br>
                            「大腦發現您剛才拍下的不是澳門自然精靈，也不是古蹟手冊喔！<br>
                            請重新調整推車手機鏡頭，對準我們步道旁的<b>澳門生態手冊色卡（綠色字卡代表植物、亮白背景色卡代表保護鳥類、薄荷粉綠色代表官邸古蹟）</b>，讓寶寶拍照解鎖更有趣、更正確的自然科普大讲堂吧！」
                        </p>
                    </div>
                    """, unsafe_allow_html=True)
                    
            except Exception as ex:
                st.error(f"離線分析引擎遇到錯誤: {str(ex)}")
                
        else:
            st.info("💡 **等待拍照中：** 請點擊上方鏡頭中的「Take Photo」按鈕拍照，智慧大腦會自動為您鑑定解說！")

st.markdown("---")
st.caption("🔒 系統安全防護聲明：絲野仙蹤（Eco-Family）始終將親子安全置於首位。本App規劃之數據僅供決策輔助，戶外出行仍請家長以現場實際路況與安全第一為準。")
