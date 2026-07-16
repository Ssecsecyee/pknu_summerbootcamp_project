# import json


# from .database import (
#     danger_collection,
#     fishing_collection
# )
# # =====================================================
# # 지역명 기반 낚시장소 검색 Tool
# # =====================================================

# async def search_fishing_spots_by_location_name(
#     location_name: str
# ) -> str:

#     """
#     사용자가 입력한 지역명 또는 장소명을 기준으로
#     MongoDB에서 낚시장소를 검색합니다.
#     """

#     if not location_name:

#         return json.dumps(
#             {
#                 "status": "location_name_required",
#                 "message": "검색할 지역명 또는 장소명이 필요합니다."
#             },
#             ensure_ascii=False
#         )


#     search_text = location_name.strip()


#     query = {

#         "$or": [

#             {
#                 "낚시터명": {
#                     "$regex": search_text,
#                     "$options": "i"
#                 }
#             },

#             {
#                 "주소": {
#                     "$regex": search_text,
#                     "$options": "i"
#                 }
#             }

#         ]

#     }


#     result = await fishing_collection.find(
#         query,
#         {
#             "_id": 0,
#             "낚시터명": 1,
#             "주소": 1
#         }
#     ).to_list(length=10)


#     fishing_spots = []


#     for spot in result:

#         fishing_spots.append(
#             {
#                 "낚시터명": spot.get(
#                     "낚시터명"
#                 ),

#                 "주소": spot.get(
#                     "주소"
#                 )
#             }
#         )


#     print(
#         "[지역 기반 낚시장소 검색]",
#         search_text
#     )

#     print(
#         "[낚시장소 검색 결과]",
#         len(fishing_spots),
#         "건"
#     )


#     return json.dumps(
#         {
#             "status": "success",

#             "search_type": "location_name",

#             "search_location": search_text,

#             "fishing_spot_count": len(
#                 fishing_spots
#             ),

#             "fishing_spots": fishing_spots
#         },

#         ensure_ascii=False,

#         indent=2
#     )
# # =====================================================
# # 4.장소명 기반 위험구역 검색 Tool
# # =====================================================

# async def search_danger_by_location_name(
#     location_name: str
# ) -> str:

#     """
#     사용자가 입력한 특정 장소명을 기준으로
#     MongoDB 위험구역 데이터를 검색합니다.
#     """

#     if not location_name:

#         return json.dumps(
#             {
#                 "status": "location_name_required",
#                 "message": "검색할 장소명이 필요합니다."
#             },
#             ensure_ascii=False
#         )


#     query = {

#         "장소명": {
#             "$regex": location_name,
#             "$options": "i"
#         }

#     }


#     result = await danger_collection.find(
#         query,
#         {
#             "_id": 0,
#             "장소명": 1,
#             "구역분류": 1,
#             "장소형태": 1,
#             "주소": 1
#         }
#     ).to_list(length=10)


#     danger_zones = []


#     for danger in result:

#         danger_zones.append(
#             {
#                 "장소명": danger.get(
#                     "장소명"
#                 ),

#                 "구역분류": danger.get(
#                     "구역분류"
#                 ),

#                 "장소형태": danger.get(
#                     "장소형태"
#                 ),

#                 "주소": danger.get(
#                     "주소"
#                 )
#             }
#         )


#     return json.dumps(
#         {
#             "status": "success",

#             "search_type": "location_name",

#             "search_location": location_name,

#             "danger": len(
#                 danger_zones
#             ) > 0,

#             "danger_count": len(
#                 danger_zones
#             ),

#             "danger_zones": danger_zones
#         },

#         ensure_ascii=False,

#         indent=2
#     )

# # =====================================================
# # 1. 낚시장소 추천 Tool
# # =====================================================

# async def get_fishing_spots(
#     lat: float | None,
#     lon: float | None
# ) -> str:

#     """
#     현재 사용자 위치를 기준으로
#     10km 이내의 가까운 낚시장소를 검색합니다.
#     """

#     # 위치 정보 확인
#     if lat is None or lon is None:

#         return json.dumps(
#             {
#                 "status": "location_required",
#                 "message": "현재 위치 정보가 필요합니다."
#             },
#             ensure_ascii=False
#         )


#     pipeline = [

#         {
#             "$geoNear": {

#                 "near": {
#                     "type": "Point",
#                     "coordinates": [
#                         lon,
#                         lat
#                     ]
#                 },

#                 "distanceField": "distance",

#                 "maxDistance": 10000,

#                 "spherical": True

#             }
#         },

#         {
#             "$limit": 5
#         },

#         {
#             "$project": {

#                 "_id": 0,

#                 "낚시터명": 1,

#                 "주소": 1,

#                 "distance": 1

#             }
#         }

#     ]


#     result = await fishing_collection.aggregate(
#         pipeline
#     ).to_list(length=5)


#     fishing_spots = []


#     for spot in result:

#         fishing_spots.append(
#             {
#                 "낚시터명": spot.get(
#                     "낚시터명"
#                 ),

#                 "주소": spot.get(
#                     "주소"
#                 ),

#                 "거리_km": round(
#                     spot.get(
#                         "distance",
#                         0
#                     ) / 1000,
#                     2
#                 )
#             }
#         )


#     return json.dumps(
#         {
#             "status": "success",

#             "search_radius_km": 10,

#             "fishing_count": len(
#                 fishing_spots
#             ),

#             "fishing_spots": fishing_spots
#         },

#         ensure_ascii=False,

#         indent=2
#     )


# # =====================================================
# # 2. 위험구역 안내 Tool
# # =====================================================

# async def get_danger_zones(
#     lat: float | None,
#     lon: float | None
# ) -> str:

#     """
#     현재 사용자 위치를 기준으로
#     500m 이내의 연안사고 위험구역을 검색합니다.
#     """

#     # 위치 정보 확인
#     if lat is None or lon is None:

#         return json.dumps(
#             {
#                 "status": "location_required",
#                 "message": "현재 위치 정보가 필요합니다."
#             },
#             ensure_ascii=False
#         )


#     pipeline = [

#         {
#             "$geoNear": {

#                 "near": {
#                     "type": "Point",
#                     "coordinates": [
#                         lon,
#                         lat
#                     ]
#                 },

#                 "distanceField": "distance",

#                 "maxDistance": 500,

#                 "spherical": True

#             }
#         },

#         {
#             "$project": {

#                 "_id": 0,

#                 "장소명": 1,

#                 "구역분류": 1,

#                 "장소형태": 1,

#                 "주소": 1,

#                 "distance": 1

#             }
#         }

#     ]


#     result = await danger_collection.aggregate(
#         pipeline
#     ).to_list(length=None)


#     danger_zones = []


#     for danger in result:

#         danger_zones.append(
#             {
#                 "장소명": danger.get(
#                     "장소명"
#                 ),

#                 "구역분류": danger.get(
#                     "구역분류"
#                 ),

#                 "장소형태": danger.get(
#                     "장소형태"
#                 ),

#                 "주소": danger.get(
#                     "주소"
#                 ),

#                 "거리_m": round(
#                     danger.get(
#                         "distance",
#                         0
#                     ),
#                     1
#                 )
#             }
#         )


#     return json.dumps(
#         {
#             "status": "success",

#             "danger": len(
#                 danger_zones
#             ) > 0,

#             "search_radius_m": 500,

#             "danger_count": len(
#                 danger_zones
#             ),

#             "danger_zones": danger_zones
#         },

#         ensure_ascii=False,

#         indent=2
#     )


# # =====================================================
# # 3. 어종 분류 Tool
# # =====================================================

# async def classify_fish(
#     image_path: str
# ):

#     """
#     업로드된 물고기 이미지를 이용하여
#     어종을 분류합니다.

#     추후 학습된 어종 분류 AI 모델을 연결합니다.
#     """

#     pass


# # =====================================================
# # 4. EXAONE Tool 명세
# # =====================================================

# tools_specification = [

#     {
#         "type": "function",

#         "function": {

#             "name": "select_fishing_tool",

#             "description": (
#                 "사용자의 질문 의도를 이해하고 "
#                 "낚시장소 추천, 위험구역 안내, "
#                 "어종 분류 또는 일반대화 중 "
#                 "하나의 카테고리로 분류합니다."
#             ),

#             "parameters": {

#                 "type": "object",

#                 "properties": {

#                     "category": {

#                         "type": "string",

#                         "enum": [
#                             "낚시장소추천",
#                             "위험구역안내",
#                             "어종분류",
#                             "일반대화"
#                         ],

#                         "description": (
#                             "현재 위치 주변 낚시장소 또는 "
#                             "낚시터 추천 요청은 '낚시장소추천', "
#                             "현재 위치 주변 위험구역, 위험한 장소 또는 "
#                             "연안사고 위험 여부 질문은 '위험구역안내', "
#                             "사진 속 물고기의 종류 또는 "
#                             "어종 판별 요청은 '어종분류', "
#                             "그 외 질문은 '일반대화'로 분류하세요."
#                         )

#                     }

#                 },

#                 "required": [
#                     "category"
#                 ]

#             }

#         }

#     }

# ]