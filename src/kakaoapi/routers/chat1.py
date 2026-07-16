from fastapi import APIRouter
from pydantic import BaseModel

from ..services.agent1 import run_fishing_agent


# =====================================================
# Chat Router
# =====================================================

router = APIRouter(
    prefix="/chat",
    tags=["AI 챗봇"]
)


# =====================================================
# 사용자 질문 요청 Schema
# =====================================================

class ChatRequest(BaseModel):

    session_id: str

    message: str

    lat: float | None = None

    lon: float | None = None

    image_path: str | None = None


# =====================================================
# AI 챗봇 API
# =====================================================

@router.post("")
async def chat(
    request: ChatRequest
):

    try:

        result = await run_fishing_agent(

            session_id=request.session_id,

            message=request.message,

            lat=request.lat,

            lon=request.lon,

            image_path=request.image_path

        )


        # =================================================
        # Agent 결과 그대로 반환
        # =================================================

        return result


    except Exception as error:

        print(
            "챗봇 오류:",
            error
        )


        return {

            "status": "error",

            "category": "error",

            "answer": (
                "AI 챗봇 응답을 처리하는 중 "
                "오류가 발생했습니다."
            )

        }