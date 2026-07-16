# src/kakaoapi/main.py
from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

# 라우터 모듈 가져오기
from .routers.upload import router as upload_router
from .routers import danger, fishing, chat1

app = FastAPI(
    title="낚시 안전 API"
)

# =====================================================
# CSS / JavaScript / Uploads 정적 파일 연결
# =====================================================
# 1. 기존 프론트엔드 자원(css, js) 마운트
app.mount(
    "/static",
    StaticFiles(directory="src/kakaoapi/static"),
    name="static"
)

# 💡 2. 업로드된 이미지가 보관될 폴더도 접근할 수 있도록 마운트 추가
# (만약 `upload.py`에서 저장하는 폴더가 루트 기준 `static/uploads`라면 아래 경로가 맞습니다)
import os
os.makedirs("src/kakaoapi/static/uploads", exist_ok=True) 


# =====================================================
# Router 연결
# =====================================================
app.include_router(danger.router)
app.include_router(fishing.router)
app.include_router(chat1.router)
app.include_router(upload_router)  


# =====================================================
# 메인 페이지
# =====================================================
@app.get("/")
async def root():
    return FileResponse(
        "src/kakaoapi/templates/location.html"
    )