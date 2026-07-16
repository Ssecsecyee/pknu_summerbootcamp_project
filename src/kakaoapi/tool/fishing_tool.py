import json

from ..database import fishing_collection


# =====================================================
# 지역명 기반 낚시장소 검색 Tool
# =====================================================



async def search_fishing_spots_by_location_name(
    location_name: str
) -> str:

    """
    사용자가 입력한 지역명 또는 장소명을 기준으로
    MongoDB에서 낚시장소를 검색합니다.
    """

    if not location_name:

        return json.dumps(
            {
                "status": "location_name_required",
                "message": "검색할 지역명 또는 장소명이 필요합니다."
            },
            ensure_ascii=False
        )

    search_text = location_name.strip()

    print(f"\n===== 검색어 =====")
    print(repr(search_text))

    query = {
        "$or": [

            {
                "낚시터명": {
                    "$regex": search_text,
                    "$options": "i"
                }
            },

            {
                "소재지도로명주소": {
                    "$regex": search_text,
                    "$options": "i"
                }
            },

            {
                "소재지지번주소": {
                    "$regex": search_text,
                    "$options": "i"
                }
            }

        ]
    }

    print("\n===== Query =====")
    print(query)

    result = await fishing_collection.find(
        query,
        {
            "_id": 0,

            "낚시터명": 1,
            "낚시터유형": 1,
            "소재지도로명주소": 1,
            "소재지지번주소": 1,
            "주요어종": 1,
            "최대수용인원": 1,
            "낚시터전화번호": 1
        }
    ).to_list(length=10)

    print("\n===== MongoDB Result =====")
    print(result)

    fishing_spots = []

    for spot in result:

        fishing_spots.append(

            {

                "낚시터명": spot.get("낚시터명"),

                "주소": (
                    spot.get("소재지도로명주소")
                    or spot.get("소재지지번주소")
                ),

                "낚시종류": spot.get("낚시터유형"),

                "주요어종": spot.get("주요어종"),

                "최대수용인원": spot.get("최대수용인원"),

                "전화번호": spot.get("낚시터전화번호")

            }

        )

    print("\n===== 최종 결과 =====")
    print(fishing_spots)

    return json.dumps(

        {

            "status": "success",

            "search_type": "location_name",

            "search_location": search_text,

            "fishing_spot_count": len(fishing_spots),

            "fishing_spots": fishing_spots

        },

        ensure_ascii=False,

        indent=2

    )

# =====================================================
# 현재 위치 기반 낚시장소 검색 Tool
# =====================================================

async def get_fishing_spots(
    lat: float | None,
    lon: float | None
) -> str:

    """
    현재 사용자 위치를 기준으로
    10km 이내의 가까운 낚시장소를 검색합니다.
    """

    if lat is None or lon is None:

        return json.dumps(
            {
                "status": "location_required",
                "message": "현재 위치 정보가 필요합니다."
            },
            ensure_ascii=False
        )


    pipeline = [

        {
            "$geoNear": {

                "near": {
                    "type": "Point",
                    "coordinates": [
                        lon,
                        lat
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

                "소재지도로명주소": 1,

                "소재지지번주소": 1,

                "주요어종": 1,

                "낚시": 1,

                "낚시터전화번호": 1,

                "distance": 1

            }
        }

    ]


    result = await fishing_collection.aggregate(
        pipeline
    ).to_list(length=5)


    fishing_spots = []


    for spot in result:

        address = (
            spot.get("소재지도로명주소")
            or spot.get("소재지지번주소")
            or "주소 정보 없음"
        )


        fishing_spots.append(
            {

                "낚시터명": spot.get(
                    "낚시터명"
                ),

                "주소": address,

                "주요어종": spot.get(
                    "주요어종"
                ),

                "낚시종류": spot.get(
                    "낚시"
                ),

                "전화번호": spot.get(
                    "낚시터전화번호"
                ),

                "거리_km": round(
                    spot.get(
                        "distance",
                        0
                    ) / 1000,
                    2
                )

            }
        )


    return json.dumps(
        {
            "status": "success",

            "search_radius_km": 10,

            "fishing_count": len(
                fishing_spots
            ),

            "fishing_spots": fishing_spots
        },

        ensure_ascii=False,

        indent=2
    )