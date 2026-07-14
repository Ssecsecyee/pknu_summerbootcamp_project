# pknu_summerboard/src/kakaoapi/database.py
from pymongo import MongoClient

try:
    # 192.168.100.5 대역의 37017 포트로 연결
    mongo_client = MongoClient("mongodb://192.168.100.5:37017/")
    db = mongo_client["fishing_db"]           # 데이터베이스 이름
    gps_logs_col = db["user_gps_logs"]        # 사용자 GPS 로그 컬렉션
    print("📡 지정된 MongoDB 서버(192.168.100.5)에 성공적으로 연결되었습니다!")
except Exception as e:
    print(f"❌ MongoDB 연결 실패: {e}")
    gps_logs_col = None