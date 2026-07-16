import json

from ..database import danger_collection


# =====================================================
# 장소명 기반 위험구역 검색 Tool
# =====================================================

async def search_danger_by_location_name(
    location_name: str
) -> str:

    """
    사용자가 입력한 특정 장소명을 기준으로
    MongoDB 위험구역 데이터를 검색합니다.
    """

    if not location_name:

        return json.dumps(
            {
                "status": "location_name_required",
                "message": "검색할 장소명이 필요합니다."
            },
            ensure_ascii=False
        )


    query = {

        "$or": [

            {
                "장소명": {
                    "$regex": location_name,
                    "$options": "i"
                }
            },

            {
                "주소": {
                    "$regex": location_name,
                    "$options": "i"
                }
            },

            {
                "장소형태": {
                    "$regex": location_name,
                    "$options": "i"
                }
            }

        ]

    }


    result = await danger_collection.find(
        query,
        {
            "_id": 0,
            "장소명": 1,
            "구역분류": 1,
            "장소형태": 1,
            "주소": 1
        }
    ).to_list(length=10)


    danger_zones = []


    for danger in result:

        danger_zones.append(
            {
                "장소명": danger.get(
                    "장소명"
                ),

                "구역분류": danger.get(
                    "구역분류"
                ),

                "장소형태": danger.get(
                    "장소형태"
                ),

                "주소": danger.get(
                    "주소"
                )
            }
        )


    return json.dumps(
        {
            "status": "success",

            "search_type": "location_name",

            "search_location": location_name,

            "danger": len(
                danger_zones
            ) > 0,

            "danger_count": len(
                danger_zones
            ),

            "danger_zones": danger_zones
        },

        ensure_ascii=False,

        indent=2
    )


# =====================================================
# 현재 위치 기반 위험구역 검색 Tool
# =====================================================

async def get_danger_zones(
    lat: float | None,
    lon: float | None
) -> str:

    """
    현재 사용자 위치를 기준으로
    500m 이내의 연안사고 위험구역을 검색합니다.
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


    result = await danger_collection.aggregate(
        pipeline
    ).to_list(length=None)


    danger_zones = []


    for danger in result:

        danger_zones.append(
            {
                "장소명": danger.get(
                    "장소명"
                ),

                "구역분류": danger.get(
                    "구역분류"
                ),

                "장소형태": danger.get(
                    "장소형태"
                ),

                "주소": danger.get(
                    "주소"
                ),

                "거리_m": round(
                    danger.get(
                        "distance",
                        0
                    ),
                    1
                )
            }
        )


    return json.dumps(
        {
            "status": "success",

            "danger": len(
                danger_zones
            ) > 0,

            "search_radius_m": 500,

            "danger_count": len(
                danger_zones
            ),

            "danger_zones": danger_zones
        },

        ensure_ascii=False,

        indent=2
    )