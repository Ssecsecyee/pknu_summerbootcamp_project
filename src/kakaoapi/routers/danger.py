from fastapi import APIRouter
from pydantic import BaseModel

from ..database import danger_collection

router = APIRouter(
    prefix="/danger",
    tags=["위험구역"]
)


# 사용자 위치 데이터
class UserLocation(BaseModel):
    lat: float
    lon: float


# 사용자 위치 기준 500m 이내 위험구역 검색
@router.post("/nearby")
async def nearby_danger(location: UserLocation):

    pipeline = [
        {
            "$geoNear": {
                "near": {
                    "type": "Point",
                    "coordinates": [
                        location.lon,
                        location.lat
                    ]
                },
                "distanceField": "distance",
                "maxDistance": 500,
                "spherical": True
            }
        },
        {
            "$project": {
                "_id": 0,
                "장소명": 1,
                "구역분류": 1,
                "장소형태": 1,
                "주소": 1,
                "distance": 1
            }
        }
    ]

    # MongoDB 공간 검색
    result = await danger_collection.aggregate(
        pipeline
    ).to_list(length=None)


    # 반환 데이터 생성
    danger_zones = []

    for danger in result:

        danger_zones.append({
            "장소명": danger.get("장소명"),
            "구역분류": danger.get("구역분류"),
            "장소형태": danger.get("장소형태"),
            "주소": danger.get("주소"),
            "거리_m": round(
                danger.get("distance", 0),
                1
            )
        })


    # 검색 결과 반환
    return {
        "danger": len(danger_zones) > 0,
        "search_radius_m": 500,
        "danger_count": len(danger_zones),
        "danger_zones": danger_zones
    }

# 터미널 실행
# python -m uvicorn app.main1:app --reload --app-dir C:\mongodb13\db_project