from fastapi import APIRouter
from pydantic import BaseModel

from ..database import fishing_collection


router = APIRouter(
    prefix="/fishing",
    tags=["낚시터 추천"]
)


# 사용자 위치 데이터
class UserLocation(BaseModel):
    lat: float
    lon: float


# 사용자 위치 기준 주변 낚시터 검색
@router.post("/nearby")
async def nearby_fishing(location: UserLocation):

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
                "maxDistance": 10000,
                "spherical": True
            }
        },
        {
            "$limit": 5
        },
        {
            "$project": {
                "_id": 0,
                "낚시터명": 1,
                "낚시터유형": 1,
                "소재지도로명주소": 1,
                "distance": 1
            }
        }
    ]

    # MongoDB 공간 검색
    result = await fishing_collection.aggregate(
        pipeline
    ).to_list(length=5)


    fishing_spots = []

    for fishing in result:

        fishing_spots.append({
            "낚시터명": fishing.get("낚시터명"),
            "낚시터유형": fishing.get("낚시터유형"),
            "주소": fishing.get("소재지도로명주소"),
            "거리_km": round(
                fishing.get("distance", 0) / 1000,
                2
            )
        })


    return {
        "search_radius_km": 10,
        "fishing_count": len(fishing_spots),
        "fishing_spots": fishing_spots
    }