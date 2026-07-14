from motor.motor_asyncio import AsyncIOMotorClient

client = AsyncIOMotorClient(
    "mongodb://192.168.100.5:37017"
)

db = client["fishing_db"]

danger_collection = db["danger_zones"]
fishing_collection = db["fishing_spots"]