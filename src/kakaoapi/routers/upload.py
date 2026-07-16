import os
import uuid
from fastapi import APIRouter, UploadFile, File

router = APIRouter()

# 💡 main.py의 static 마운트 경로와 일치하도록 절대 경로 계산
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) # src/kakaoapi
UPLOAD_DIR = os.path.join(BASE_DIR, "static", "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post("/api/upload-image")
async def upload_image(file: UploadFile = File(...)):
    try:
        file_extension = os.path.splitext(file.filename)[1]
        unique_filename = f"{uuid.uuid4()}{file_extension}"
        file_path = os.path.join(UPLOAD_DIR, unique_filename)
        
        with open(file_path, "wb") as buffer:
            buffer.write(await file.read())
            
        # 💡 프론트엔드와 YOLO 모델이 접근할 수 있는 경로 반환
        return {
            "status": "success",
            "image_path": file_path
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}