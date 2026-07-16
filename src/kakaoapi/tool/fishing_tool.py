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


    query = {

        "$or": [

            {
                "낚시터명": {
                    "$regex": search_text,
                    "$options": "i"
                }
            },

            {
                "주소": {
                    "$regex": search_text,
                    "$options": "i"
                }
            }

        ]

    }


    result = await fishing_collection.find(
        query,
        {
            "_id": 0,
            "낚시터명": 1,
            "주소": 1
        }
    ).to_list(length=10)


    fishing_spots = []


    for spot in result:

        fishing_spots.append(
            {
                "낚시터명": spot.get(
                    "낚시터명"
                ),

                "주소": spot.get(
                    "주소"
                )
            }
        )


    print(
        "[지역 기반 낚시장소 검색]",
        search_text
    )

    print(
        "[낚시장소 검색 결과]",
        len(fishing_spots),
        "건"
    )


    return json.dumps(
        {
            "status": "success",

            "search_type": "location_name",

            "search_location": search_text,

            "fishing_spot_count": len(
                fishing_spots
            ),

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

                "주소": 1,

                "distance": 1

            }
        }

    ]


    result = await fishing_collection.aggregate(
        pipeline
    ).to_list(length=5)


    fishing_spots = []


    for spot in result:

        fishing_spots.append(
            {
                "낚시터명": spot.get(
                    "낚시터명"
                ),

                "주소": spot.get(
                    "주소"
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