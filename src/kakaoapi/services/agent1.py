import json

from openai import OpenAI
from pydantic import ValidationError

from ..schemas.schemas1 import FishingAssistantQuerySchema

from ..tool import (
    search_fishing_spots_by_location_name,
    search_danger_by_location_name,
    get_fishing_spots,
    get_danger_zones,
    classify_fish
)


# =====================================================
# EXAONE API 설정
# =====================================================

BASE_URL = "http://10.174.96.119:18000/v1"

MODEL_NAME = "LGAI-EXAONE/EXAONE-3.5-7.8B-Instruct"


client = OpenAI(
    base_url=BASE_URL,
    api_key="no_key"
)


# =====================================================
# 사용자별 대화 기록
# =====================================================

chat_sessions = {}

# =====================================================
# 챗봇 기본 역할 Prompt
# =====================================================

SYSTEM_PROMPT = """
당신은 '낚시 안전 가이드' AI 챗봇입니다.

사용자의 낚시 관련 질문을 이해하고
쉽고 친절하게 설명하는 역할을 합니다.

주요 기능은 다음과 같습니다.

1. 낚시장소 추천
- 사용자 위치를 기준으로 주변 낚시장소 정보를 안내합니다.

2. 위험구역 안내
- 특정 장소 또는 사용자 현재 위치 주변의
  연안사고 위험구역 정보를 안내합니다.

3. 어종 분류
- 사용자가 제공한 물고기 이미지를 기반으로
  어종 분류 결과를 안내합니다.

4. 일반 낚시 질문
- 낚시 방법, 준비물, 장비, 안전 수칙 등
  일반적인 낚시 관련 질문에 답변합니다.

낚시장소 또는 위험구역 검색 기능의 결과가 제공된 경우
반드시 제공된 검색 결과를 기준으로 답변하세요.

검색 결과에 존재하지 않는 장소,
위험구역 또는 데이터를 임의로 만들어내지 마세요.

검색 결과가 없으면
등록된 정보를 찾을 수 없다고 솔직하게 설명하세요.

사용자가 이해하기 쉽도록 한국어로 답변하세요.

답변은 핵심 내용을 먼저 설명하고,
필요한 경우 항목별로 정리하세요.

너무 길고 불필요한 설명은 피하세요.
"""
# =====================================================
# 챗봇 기본 역할
# =====================================================
CLASSIFICATION_PROMPT = """
당신은 낚시 안전 챗봇의 사용자 질문 분류 AI입니다.

사용자의 질문을 분석하여 반드시 다음 JSON 형식으로만 답변하세요.

{
    "category": "카테고리",
    "location_name": null,
    "use_current_location": false
}


=====================================================
카테고리
=====================================================

category는 반드시 다음 4개 중 하나입니다.

1. 낚시장소추천
2. 위험구역안내
3. 어종분류
4. 일반대화


=====================================================
1. 낚시장소추천
=====================================================

사용자가 낚시할 장소, 낚시터, 낚시 포인트를
찾거나 추천받으려는 질문입니다.

다음과 같은 표현을 포함합니다.

- 낚시할 곳
- 낚시하기 좋은 곳
- 낚시터
- 낚시 포인트
- 낚싯대 펼 만한 곳
- 낚시 장소 추천
- 어디서 낚시해
- 어디가 좋아
- 낚시 갈 곳
- 낚시 가능한 곳

예시:

"거제에서 낚시할 만한 곳 추천해줘"

{
    "category": "낚시장소추천",
    "location_name": "거제",
    "use_current_location": false
}


"통영 쪽에서 낚싯대 펼 만한 곳 있어?"

{
    "category": "낚시장소추천",
    "location_name": "통영",
    "use_current_location": false
}


"주변에 낚싯대 펼 만한 곳 있어?"

{
    "category": "낚시장소추천",
    "location_name": null,
    "use_current_location": true
}


"근처에 낚시할 곳 있어?"

{
    "category": "낚시장소추천",
    "location_name": null,
    "use_current_location": true
}


"가까운 낚시터 추천해줘"

{
    "category": "낚시장소추천",
    "location_name": null,
    "use_current_location": true
}


=====================================================
2. 위험구역안내
=====================================================

사용자가 특정 장소 또는 현재 위치 주변의
위험구역, 안전 여부, 사고 위험을 확인하려는 질문입니다.

다음과 같은 표현을 포함합니다.

- 위험구역
- 위험한 곳
- 안전해
- 안전한가
- 사고 위험
- 여기 위험해
- 주변 위험구역
- 근처 위험구역

예시:

"봉길 갯바위 주변에 위험구역 있어?"

{
    "category": "위험구역안내",
    "location_name": "봉길 갯바위",
    "use_current_location": false
}


"해금강선착장 좌측 갯바위에서 낚시해도 안전해?"

{
    "category": "위험구역안내",
    "location_name": "해금강선착장 좌측 갯바위",
    "use_current_location": false
}


"주변에 위험구역 있어?"

{
    "category": "위험구역안내",
    "location_name": null,
    "use_current_location": true
}


"여기서 낚시해도 안전해?"

{
    "category": "위험구역안내",
    "location_name": null,
    "use_current_location": true
}


=====================================================
3. 어종분류
=====================================================

사용자가 물고기 사진, 이미지 파일(jpeg, png 등)을 업로드하거나, 
이미지를 기반으로 어종을 확인/분류해 달라고 요청하는 질문입니다.

다음과 같은 상황이나 표현을 포함합니다.

- 사진/이미지 파일이 전송되거나 언급된 경우
- 무슨 물고기야
- 어떤 물고기야
- 어종 알려줘 / 어종 분류해줘
- 물고기 종류가 뭐야?
- 내가 잡은 물고기 이름이 뭐야?
- 이 물고기 먹어도 되는 거야? 무슨 종류야?
- [사진] 이거 뭐야?

예시:

"이 물고기 무슨 어종이야?"

""

{
    "category": "어종분류",
    "location_name": null,
    "use_current_location": false
}


=====================================================
4. 일반대화
=====================================================

위 세 가지 기능과 직접적인 관련이 없는 질문입니다.

예시:

"안녕"

{
    "category": "일반대화",
    "location_name": null,
    "use_current_location": false
}


"낚시 초보인데 준비물이 뭐야?"

{
    "category": "일반대화",
    "location_name": null,
    "use_current_location": false
}


=====================================================
location_name 판단 규칙
=====================================================

사용자가 특정 지역명, 장소명, 주소 또는 지명을
직접 언급한 경우 해당 장소를 location_name에 작성하세요.

예:

거제
통영
부산
기장
해운대
봉길 갯바위
해금강선착장 좌측 갯바위

특정 장소가 언급되지 않은 경우:

"location_name": null


=====================================================
use_current_location 판단 규칙
=====================================================

사용자가 자신의 현재 위치를 기준으로
주변, 근처 또는 가까운 장소를 찾으려는 경우
반드시 use_current_location을 true로 설정하세요.

다음 표현은 반드시 현재 위치 기준 표현으로 판단하세요.

- 주변
- 주변에
- 내 주변
- 현재 위치
- 지금 위치
- 여기
- 여기서
- 이 근처
- 근처
- 근처에
- 가까운
- 가까이
- 가까운 곳
- 제일 가까운
- 가장 가까운
- 지금 근처
- 내 위치 기준

중요:

사용자가 특정 지역명 또는 장소명을 언급하지 않았고
"주변", "근처", "가까운", "여기" 등의 표현을 사용하면
반드시 다음과 같이 분류하세요.

"use_current_location": true

예시:

"주변에 낚싯대 펼 만한 곳 있어?"
→ use_current_location = true

"근처 낚시터 알려줘"
→ use_current_location = true

"가까운 낚시 장소 추천해줘"
→ use_current_location = true

"여기서 낚시해도 안전해?"
→ use_current_location = true


=====================================================
중요 규칙
=====================================================

1. 반드시 JSON 형식으로만 답변하세요.

2. JSON 앞뒤에 설명을 작성하지 마세요.

3. Markdown 코드 블록을 사용하지 마세요.

4. category는 반드시 지정된 4개 카테고리 중 하나여야 합니다.

5. 특정 장소명이 있으면 location_name에 장소명을 작성하세요.

6. 특정 장소명이 없고 주변, 근처, 가까운 곳, 여기 등의 표현이 있으면
   반드시 use_current_location을 true로 설정하세요.

7. 특정 장소명이 있으면 use_current_location은 false입니다.

8. location_name이 null이고 현재 위치 기준 표현이 있으면
   use_current_location은 반드시 true입니다.
"""


# =====================================================
# 질문 의도 분류
# =====================================================

def classify_user_question(
    message: str
) -> FishingAssistantQuerySchema:

    # -------------------------------------------------
    # 분류 전용 사용자 요청
    # -------------------------------------------------

    classification_request = f"""
다음 사용자 질문을 분석하세요.

사용자 질문:
{message}

당신의 작업은 질문에 답변하는 것이 아닙니다.
사용자의 질문 의도와 장소 기준만 분석하세요.

반드시 JSON 객체 하나만 출력하세요.

출력 형식:

{{
    "category": "카테고리",
    "location_name": null,
    "use_current_location": false
}}

category는 반드시 다음 중 하나입니다.

- 낚시장소추천
- 위험구역안내
- 어종분류
- 일반대화

특정 장소명이 질문에 포함되어 있다면
location_name에 장소명을 작성하세요.

"내 주변", "여기", "현재 위치"처럼
사용자의 현재 위치를 의미한다면
use_current_location을 true로 설정하세요.

질문에 직접 답변하지 마세요.
설명하지 마세요.
추천하지 마세요.
마크다운을 사용하지 마세요.

JSON 객체 하나만 출력하세요.
"""


    # -------------------------------------------------
    # EXAONE 질문 분류 요청
    # -------------------------------------------------

    classification_response = (
        client.chat.completions.create(
            model=MODEL_NAME,

            messages=[
                {
                    "role": "system",
                    "content": CLASSIFICATION_PROMPT
                },
                {
                    "role": "user",
                    "content": classification_request
                }
            ],

            temperature=0,

            max_tokens=150
        )
    )


    classification_text = (
        classification_response
        .choices[0]
        .message
        .content
    )


    print(
        "EXAONE 분류 원본:",
        classification_text
    )


    # -------------------------------------------------
    # JSON 문자열 정리
    # -------------------------------------------------

    classification_text = (
        classification_text
        .strip()
    )


    # Markdown JSON 코드 블록 제거
    classification_text = (
        classification_text
        .replace("```json", "")
        .replace("```JSON", "")
        .replace("```", "")
        .strip()
    )


    # -------------------------------------------------
    # JSON 객체 부분 추출
    # -------------------------------------------------

    json_start = classification_text.find("{")

    json_end = classification_text.rfind("}")


    if (
        json_start != -1
        and json_end != -1
        and json_end > json_start
    ):

        classification_text = (
            classification_text[
                json_start:json_end + 1
            ]
        )


    print(
        "JSON 추출 결과:",
        classification_text
    )


    # -------------------------------------------------
    # JSON → Schema 검증
    # -------------------------------------------------

    try:

        classification_data = json.loads(
            classification_text
        )


        query_schema = (
            FishingAssistantQuerySchema(
                **classification_data
            )
        )


        return query_schema


    except (
        json.JSONDecodeError,
        ValidationError,
        TypeError
    ) as error:

        print(
            "질문 분류 오류:",
            error
        )


        return FishingAssistantQuerySchema(
            category="일반대화",
            location_name=None,
            use_current_location=False
        )

# =====================================================
# Agent 실행
# =====================================================

async def run_fishing_agent(
    session_id: str,
    message: str,
    lat: float | None = None,
    lon: float | None = None,
    image_path: str | None = None
):

    # -------------------------------------------------
    # 1. 사용자 세션 생성
    # -------------------------------------------------

    if session_id not in chat_sessions:

        chat_sessions[session_id] = [
            {
                "role": "system",
                "content": SYSTEM_PROMPT
            }
        ]


    messages = chat_sessions[session_id]


    # -------------------------------------------------
    # 2. 사용자 질문 저장
    # -------------------------------------------------

    messages.append(
        {
            "role": "user",
            "content": message
        }
    )


    # -------------------------------------------------
    # 3. EXAONE 질문 의도 분류
    # -------------------------------------------------

    query_schema = classify_user_question(
        message=message
    )


    category = query_schema.category

    location_name = query_schema.location_name

    use_current_location = query_schema.use_current_location


    print(
        "질문 카테고리:",
        category
    )

    print(
        "추출 장소명:",
        location_name
    )

    print(
        "현재 위치 사용:",
        use_current_location
    )


    # -------------------------------------------------
    # 4. Category에 따른 Tool 실행
    # -------------------------------------------------

    tool_result = None


    if category == "낚시장소추천":

        # 특정 지역명 또는 장소명이 있는 경우
        if location_name:

            print(
                "[Tool 선택] "
                "search_fishing_spots_by_location_name"
            )


            tool_result = (
                await search_fishing_spots_by_location_name(
                    location_name=location_name
                )
            )


        # 현재 위치 기준 질문
        elif use_current_location:

            print(
                "[Tool 선택] get_fishing_spots"
            )


            tool_result = await get_fishing_spots(
                lat=lat,
                lon=lon
            )


        # 검색 기준이 없는 경우
        else:

            tool_result = json.dumps(
                {
                    "status": "location_required",

                    "message": (
                        "낚시장소를 추천하려면 "
                        "지역명 또는 현재 위치 정보가 필요합니다."
                    )
                },

                ensure_ascii=False
            )


    elif category == "위험구역안내":

        # 특정 장소명이 있는 경우
        if location_name:

            tool_result = (
                await search_danger_by_location_name(
                    location_name=location_name
                )
            )


        # 현재 위치 기준 질문
        elif use_current_location:

            tool_result = await get_danger_zones(
                lat=lat,
                lon=lon
            )


        # 장소명과 현재 위치 기준이 모두 없는 경우
        else:

            tool_result = json.dumps(
                {
                    "status": "location_required",
                    "message": (
                        "위험구역을 확인하려면 "
                        "장소명 또는 현재 위치 정보가 필요합니다."
                    )
                },
                ensure_ascii=False
            )


    elif category == "어종분류":

        if image_path is None:

            tool_result = json.dumps(
                {
                    "status": "image_required",
                    "message": (
                        "어종 분류를 위해 "
                        "물고기 이미지가 필요합니다."
                    )
                },
                ensure_ascii=False
            )

        else:

            tool_result = await classify_fish(
                image_path=image_path
            )

    # -------------------------------------------------
    # 4-2. 위치 정보 필요 여부 확인
    # -------------------------------------------------

    if tool_result is not None:

        try:

            parsed_tool_result = json.loads(
                tool_result
            )


            if (
                parsed_tool_result.get("status")
                == "location_required"
            ):

                return {
                    "status": "location_required",

                    "category": category,

                    "answer": parsed_tool_result.get(
                        "message",
                        "현재 위치 정보가 필요합니다."
                    )
                }


        except json.JSONDecodeError:

            pass
    # -------------------------------------------------
    # 5. Tool 결과가 있는 경우 EXAONE에 전달
    # -------------------------------------------------

    if tool_result is not None:

        print("========== TOOL RESULT ==========")
        print(tool_result)
        print("=================================")

        final_messages = messages + [

            {
                "role": "system",

                "content": f"""
    당신은 낚시 안전 전문 AI입니다.

    아래는 MongoDB에서 검색된 실제 데이터입니다.

    ==============================
    DB 검색 결과
    ==============================

    {tool_result}

    ==============================

    규칙

    1. 반드시 위 DB 검색 결과만 사용하여 답변하세요.

    2. DB에 있는 정보만 설명하세요.

    3. 검색 결과에 없는 내용을 추측하거나 생성하지 마세요.

    4. 주소가 존재하면 반드시 주소를 포함하세요.

    5. 낚시터명, 주소, 거리 등의 정보를 자연스럽게 설명하세요.

    6. DB 검색 결과가 있다면 '정보가 없습니다'라고 답하면 안 됩니다.

    7. 사용자의 질문에 맞게 위 정보를 자연스럽게 요약해서 답변하세요.
    """
            }

        ]

    else:

        final_messages = messages


    # -------------------------------------------------
    # 6. 최종 자연어 답변 생성
    # -------------------------------------------------

    final_response = (
        client.chat.completions.create(
            model=MODEL_NAME,

            messages=final_messages,

            temperature=0.3,

            max_tokens=700
        )
    )


    answer = (
        final_response
        .choices[0]
        .message
        .content
    )


    # -------------------------------------------------
    # 7. AI 답변 대화 기록 저장
    # -------------------------------------------------

    messages.append(
        {
            "role": "assistant",
            "content": answer
        }
    )


    # -------------------------------------------------
    # 8. 대화 기록 길이 제한
    # -------------------------------------------------

    limit_chat_history(
        messages
    )


    return {
        "status": "success",
        "category": category,
        "answer": answer
    }


# =====================================================
# 대화 기록 길이 제한
# =====================================================

def limit_chat_history(
    messages: list
):

    system_message = messages[0]

    conversation = messages[1:]


    # 최근 20개 메시지만 유지
    if len(conversation) > 20:

        conversation = conversation[-20:]


    messages.clear()


    messages.append(
        system_message
    )


    messages.extend(
        conversation
    )