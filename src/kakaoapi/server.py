from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import geopandas as gpd
import pandas as pd
from shapely.geometry import Point
from pymongo import MongoClient
import datetime

app = FastAPI()

# 🌐 CORS 설정: 프론트엔드(HTML)에서 이 파이썬 서버로 데이터를 보낼 수 있도록 허용
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 💾 1. [수정 완료] 제공해주신 실제 원격 MongoDB 주소 연동
try:
    # 192.168.100.5 대역의 37017 포트로 연결합니다.
    mongo_client = MongoClient("mongodb://192.168.100.5:37017/")
    db = mongo_client["fishing_db"]           # 데이터베이스 이름
    gps_logs_col = db["user_gps_logs"]        # 사용자 GPS 로그가 누적될 컬렉션
    print("📡 지정된 MongoDB 서버(192.168.100.5)에 성공적으로 연결되었습니다!")
except Exception as e:
    print(f"❌ MongoDB 연결 실패: {e}")

# 📍 2. GeoPandas 공간 데이터 로드 (서버 구동 시 최초 1회 실행)
print("🗺️ 부산시 공간 분석 데이터를 로딩 중입니다...")
fishing_df = pd.read_csv("C:/mongo_data/data/낚시터정보_부산광역시.csv", encoding="cp949")
fishing_gdf = gpd.GeoDataFrame(fishing_df, geometry=gpd.points_from_xy(fishing_df["WGS84경도"], fishing_df["WGS84위도"]), crs="EPSG:4326")
fishing_m = fishing_gdf.to_crs(epsg=5179)
fish_name_col = "낚시터명" if "낚시터명" in fishing_gdf.columns else fishing_gdf.columns[0]

danger_df = pd.read_excel("C:/mongo_data/data/연안사고위험구역_좌표변환.xlsx").dropna(subset=["경도", "위도"])
danger_gdf = gpd.GeoDataFrame(danger_df, geometry=gpd.points_from_xy(danger_df["경도"], danger_df["위도"]), crs="EPSG:4326")
danger_m = danger_gdf.to_crs(epsg=5179)
danger_name_col = "장소명" if "장소명" in danger_df.columns else danger_df.columns[0]


# 📥 프론트엔드 데이터 수신 양식 정의
class UserLocation(BaseModel):
    longitude: float
    latitude: float

# 🚀 3. 실시간 위치 분석 및 MongoDB 로그 적재 API
@app.post("/analyze")
def analyze_and_log_location(location: UserLocation):
    user_lon = location.longitude
    user_lat = location.latitude
    
    # --------------------------------------------------
    # [A] MongoDB에 실시간 사용자 GPS 요청 로그 데이터 insert
    # --------------------------------------------------
    log_data = {
        "latitude": user_lat,
        "longitude": user_lon,
        "timestamp": datetime.datetime.now() # 로그가 수신된 서버 현재 시간
    }
    inserted_id = gps_logs_col.insert_one(log_data).inserted_id
    
    # --------------------------------------------------
    # [B] GeoPandas 기반 사용자 주변 1km(1000m) 공간 스캔 및 분석
    # --------------------------------------------------
    user_point = gpd.GeoSeries([Point(user_lon, user_lat)], crs="EPSG:4326").to_crs(epsg=5179).iloc[0]
    
    fish_distances = fishing_m['geometry'].distance(user_point)
    danger_distances = danger_m['geometry'].distance(user_point)
    
    search_radius = 1000
    nearby_fish = fishing_m[fish_distances <= search_radius].copy()
    nearby_danger = danger_m[danger_distances <= search_radius].copy()
    
    nearby_fish['distance'] = fish_distances[fish_distances <= search_radius]
    nearby_danger['distance'] = danger_distances[danger_distances <= search_radius]
    
    # --------------------------------------------------
    # [C] 챗봇 UI 화면으로 돌려줄 결과 메시지 빌드 (HTML 서식 적용)
    # --------------------------------------------------
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
        
    # 최종 데이터 리턴
    return {
        "status": "success",
        "mongo_log_id": str(inserted_id),
        "reply": reply_html
    }