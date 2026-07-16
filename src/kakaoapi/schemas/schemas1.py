from pydantic import BaseModel, Field
from typing import Literal


# =====================================================
# 사용자 질문 이해 Schema
# =====================================================

class FishingAssistantQuerySchema(BaseModel):

    category: Literal[
        "낚시장소추천",
        "위험구역안내",
        "어종분류",
        "일반대화"
    ] = Field(
        default="일반대화",
        description=(
            "사용자의 질문 의도를 분류합니다."
        )
    )


    location_name: str | None = Field(
        default=None,
        description=(
            "사용자가 질문에서 언급한 특정 장소명입니다. "
            "특정 장소가 없다면 null입니다."
        )
    )


    use_current_location: bool = Field(
        default=False,
        description=(
            "사용자가 내 주변, 여기, 현재 위치 등 "
            "자신의 현재 위치를 기준으로 질문하는 경우 true입니다."
        )
    )