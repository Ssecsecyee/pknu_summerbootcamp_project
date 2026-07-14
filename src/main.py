# pknu_summerboard/src/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.kakaoapi.routers.location import router as location_router

app = FastAPI(title="Fishing Safety Analysis Server")

# 🌐 CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 🔌 분리한 kakaoapi 라우터 등록
app.include_router(location_router)

@app.get("/")
def read_root():
    return {"message": "낚시 안전 분석 서버가 정상 작동 중입니다."}