# src/kakaoapi/tool/yolo_tool.py
import os
import json
import asyncio  # 비동기 처리를 위해 추가
from ultralytics import YOLO

# YOLO 모델 경로 설정
MODEL_PATH = os.path.join(os.path.dirname(__file__), "../../../yolov26_weigths/best.pt")

try:
    model = YOLO(MODEL_PATH)
except Exception as e:
    print(f"YOLO 모델 로드 실패: {e}")
    model = None

# 1. Agent 메인 코드와 맞추기 위해 함수명을 'classify_fish'로 변경하고 'async def' 선언
async def classify_fish(image_path: str) -> str:
    """
    이미지 경로를 받아 YOLO 모델을 돌린 뒤 결과를 JSON 문자열로 반환합니다.
    Agent 메인 코드에서 json.loads()로 파싱하므로 return 값을 json.dumps()로 직렬화합니다.
    """
    if model is None:
        return json.dumps({"status": "error", "message": "YOLO 모델이 로드되지 않았습니다."}, ensure_ascii=False)
    
    if not os.path.exists(image_path):
        return json.dumps({"status": "error", "message": f"이미지 파일을 찾을 수 없습니다: {image_path}"}, ensure_ascii=False)
        
    try:
        # 2. 동기 함수인 model(image_path)를 비동기 이벤트 루프 내에서 안전하게 실행 (병목 방지)
        loop = asyncio.get_event_loop()
        results = await loop.run_in_executor(None, lambda: model(image_path))
        
        detected_fish = []
        
        for result in results:
            for box in result.boxes:
                class_id = int(box.cls[0])
                class_name = model.names[class_id]
                confidence = float(box.conf[0])
                
                detected_fish.append({
                    "species": class_name,
                    "confidence": f"{round(confidence * 100, 1)}%"  # EXAONE이 알아보기 쉽게 퍼센트(%)로 변환
                })
        
        # 물고기가 하나도 탐지되지 않은 경우의 처리
        if not detected_fish:
            return json.dumps({
                "status": "no_detection", 
                "message": "이미지에서 인식된 물고기가 없습니다."
            }, ensure_ascii=False)
                
        # 3. Agent 메인 코드의 json.loads() 흐름에 맞추기 위해 json.dumps로 반환
        return json.dumps({
            "status": "success",
            "data": detected_fish
        }, ensure_ascii=False)
        
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)}, ensure_ascii=False)