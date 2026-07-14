# pknu_summerboard/src/kakaoapi/routers/location.py
from fastapi import APIRouter
import datetime
from src.kakaoapi.database import gps_logs_col
from src.kakaoapi.schemas.location import UserLocation
from src.kakaoapi.services.geo_service import scan_nearby_safety

router = APIRouter()

@router.post("/analyze")
def analyze_and_log_location(location: UserLocation):
    user_lon = location.longitude
    user_lat = location.latitude
    
    # [A] MongoDB 로그 적재
    inserted_id = None
    if gps_logs_col is not None:
        log_data = {
            "latitude": user_lat,
            "longitude": user_lon,
            "timestamp": datetime.datetime.now()
        }
        inserted_id = gps_logs_col.insert_one(log_data).inserted_id
    
    # [B] GeoPandas 서비스 호출하여 분석 HTML 결과 획득
    reply_html = scan_nearby_safety(user_lon, user_lat)
    
    return {
        "status": "success",
        "mongo_log_id": str(inserted_id) if inserted_id else "failed",
        "reply": reply_html
    }