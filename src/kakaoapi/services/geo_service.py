# pknu_summerboard/src/kakaoapi/services/geo_service.py
import os
import time
import requests
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point
from shapely.ops import nearest_points

# 📂 데이터 경로 설정 (기존 C드라이브 경로 유지하되, 필요시 상대경로 변경 가능)
FISHING_PATH = "C:/mongo_data/data/낚시터정보_부산광역시.csv"
DANGER_PATH = "C:/mongo_data/data/연안사고위험구역_좌표변환.xlsx"

print("🗺️ [Service] 부산시 공간 분석 데이터를 로딩 중입니다...")
# 낚시터 데이터 로드 및 초기화
fishing_df = pd.read_csv(FISHING_PATH, encoding="cp949")
fishing_gdf = gpd.GeoDataFrame(fishing_df, geometry=gpd.points_from_xy(fishing_df["WGS84경도"], fishing_df["WGS84위도"]), crs="EPSG:4326")
fishing_m = fishing_gdf.to_crs(epsg=5179)
fish_name_col = "낚시터명" if "낚시터명" in fishing_gdf.columns else fishing_gdf.columns[0]

# 위험구역 데이터 로드 및 초기화
danger_df = pd.read_excel(DANGER_PATH).dropna(subset=["경도", "위도"])
danger_gdf = gpd.GeoDataFrame(danger_df, geometry=gpd.points_from_xy(danger_df["경도"], danger_df["위도"]), crs="EPSG:4326")
danger_m = danger_gdf.to_crs(epsg=5179)
danger_name_col = "장소명" if "장소명" in danger_df.columns else danger_df.columns[0]

# ==========================================
# 1. 실시간 반경 Scan 및 HTML 응답 생성 로직 (기존 server.py 로직)
# ==========================================
def scan_nearby_safety(user_lon: float, user_lat: float, search_radius: int = 1000):
    user_point = gpd.GeoSeries([Point(user_lon, user_lat)], crs="EPSG:4326").to_crs(epsg=5179).iloc[0]
    
    fish_distances = fishing_m['geometry'].distance(user_point)
    danger_distances = danger_m['geometry'].distance(user_point)
    
    nearby_fish = fishing_m[fish_distances <= search_radius].copy()
    nearby_danger = danger_m[danger_distances <= search_radius].copy()
    
    nearby_fish['distance'] = fish_distances[fish_distances <= search_radius]
    nearby_danger['distance'] = danger_distances[danger_distances <= search_radius]
    
    reply_html = ""
    
    # ① 위험 구역 체크 결과
    if not nearby_danger.empty:
        reply_html += "❌ <b>[위험 알림] 주의하세요! 주변에 사고 위험구역이 감지되었습니다.</b><br>"
        for _, row in nearby_danger.sort_values(by='distance').iterrows():
            reply_html += f"⚠️ '{row[danger_name_col]}' 구역이 회원님 위치와 약 {row['distance']:.1f}m 거리에 있습니다.<br>"
    else:
        reply_html += "✅ <b>[안전] 현재 위치 주변 1km 이내에 지정된 연안사고 위험구역은 없습니다.</b><br>"
        
    reply_html += "<hr style='border: 0; border-top: 1px dashed #ccc; margin: 8px 0;'>"
    
    # ② 주변 공식 낚시터 추천 및 안전성 검사 결과
    if not nearby_fish.empty:
        reply_html += f"🎣 <b>이용 가능한 주변 공식 낚시터 ({len(nearby_fish)}곳):</b><br>"
        for _, row in nearby_fish.sort_values(by='distance').iterrows():
            dists_from_this_fish = danger_m['geometry'].distance(row['geometry'])
            is_fish_dangerous = dists_from_this_fish.min() <= 500
            safety_icon = "⚠️(위험구역 인접)" if is_fish_dangerous else "🍏(안전 영역)"
            
            reply_html += f"📍 '{row[fish_name_col]}' ({row['distance']:.1f}m 거리) {safety_icon}<br>"
    else:
        reply_html += "ℹ️ 반경 1km 이내에 등록된 공식 낚시터가 존재하지 않습니다.<br>"
        
    return reply_html

# ==========================================
# 2. 주소 -> 위경도 변환 로직 (기존 geocode_danger.py 로직)
# ==========================================
def address_to_coord(address: str):
    KAKAO_API_KEY = "d40c2af9123125bb64cd913a8906a574"
    url = "https://dapi.kakao.com/v2/local/search/address.json"
    headers = {"Authorization": f"KakaoAK {KAKAO_API_KEY}"}
    
    try:
        response = requests.get(url, headers=headers, params={"query": address})
        data = response.json()
        if data.get("documents"):
            return data["documents"][0]["x"], data["documents"][0]["y"]
    except Exception as e:
        print(f"API 요청 오류: {e}")
    return None, None