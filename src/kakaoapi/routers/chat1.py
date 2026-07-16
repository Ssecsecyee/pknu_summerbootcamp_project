import os
from fastapi import APIRouter
from pydantic import BaseModel
from PIL import Image

from ..services.agent1 import run_fishing_agent

# =====================================================
# YOLO 모델 로드 (지정하신 정확한 경로 반영)
# =====================================================
try:
    from ultralytics import YOLO
    
    # 실행 디렉터리(C:\pknu_summerbootcamp_project) 획득
    PROJECT_ROOT = os.getcwd() 
    
    # 알려주신 경로 구조(src/yolov26_weigths/best.pt) 병합
    model_path = os.path.join(PROJECT_ROOT, "src", "yolov26_weigths", "best.pt")
    
    # 파일이 진짜 존재하는지 확인 후 로드
    if os.path.exists(model_path):
        yolo_model = YOLO(model_path)
        print(f"✅ 라우터에 YOLO 비전 모델 로드 성공! ({model_path})")
    else:
        yolo_model = None
        print(f"⚠️ YOLO 모델 파일({model_path})을 찾을 수 없습니다. 경로를 다시 확인해주세요.")
        
except Exception as e:
    yolo_model = None
    print(f"❌ YOLO 비전 모델 로드 중 오류 발생: {e}")


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
        # 1단계: 유저가 보낸 원래 질문을 기본 메시지로 설정
        user_prompt = request.message if request.message.strip() else "(사진 분석 요청)"
        
        # 2단계: 이미지 분석 결과에 따른 사전 텍스트 가공
        vision_context = ""
        
        if request.image_path and yolo_model:
            if os.path.exists(request.image_path):
                try:
                    img = Image.open(request.image_path)
                    yolo_results = yolo_model(img)
                    
                    detected_fish = []
                    for result in yolo_results:
                        for box in result.boxes:
                            c_id = int(box.cls[0])
                            c_name = yolo_model.names[c_id]
                            conf = float(box.conf[0])
                            
                            # 신뢰도가 50% 이상인 경우에만 결과로 인정
                            if conf > 0.5:
                                detected_fish.append(c_name)
                    
                    if detected_fish:
                        fish_names = ", ".join(list(set(detected_fish)))
                        vision_context = f"[비전 모델(YOLO) 분석 결과: 사진에서 '{fish_names}' 탐지됨]"
                    else:
                        vision_context = "[비전 모델(YOLO) 분석 결과: 물고기 어종을 감지하지 못함]"
                        
                except Exception as yolo_err:
                    print("YOLO 처리 중 오류 발생 (무시하고 진행):", yolo_err)
                    vision_context = "[비전 모델(YOLO) 분석 결과: 시스템 오류로 이미지 분석 실패]"
            else:
                print(f"⚠️ 업로드된 이미지 경로를 찾을 수 없음: {request.image_path}")
                vision_context = "[비전 모델(YOLO) 분석 결과: 서버 내 이미지 파일 유실]"

        # 3단계: 순차적으로 에이전트에 주입할 텍스트 빌드 (구조화된 템플릿 코드)
        # LLM이 헷갈리지 않게 유저 질문과 시스템 정보를 순서대로 명확히 나누어 줍니다.
        if vision_context:
            final_message = (
                f"■ 사용자 요청 문장:\n{user_prompt}\n\n"
                f"■ 시스템 참조 데이터:\n{vision_context}\n\n"
                f"⚠️ 지침: 위 참조 데이터를 기반으로 사용자의 질문이나 요구사항에 맞춰 관련 정보(어종 판별 결과, 규정, 금어기 등)를 차근차근 순서대로 친절하게 답변하세요."
            )
        else:
            final_message = user_prompt

        # =================================================
        # 🚀 순차 가공된 메시지를 들고 기존 에이전트 서비스 호출
        # =================================================
        result = await run_fishing_agent(

            session_id=request.session_id,

            message=final_message, # 차근차근 조립된 텍스트 주입

            lat=request.lat,

            lon=request.lon,

            image_path=request.image_path

        )

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