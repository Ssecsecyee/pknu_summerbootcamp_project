from pymongo import MongoClient

# MongoDB 연결 설정
MONGO_URI = "mongodb://192.168.100.40:27017"
client = MongoClient(MONGO_URI)

# DB 선택
db = client['fishing_db']

def get_db():
    return db