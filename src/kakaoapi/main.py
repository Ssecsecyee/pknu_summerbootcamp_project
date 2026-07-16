from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .routers import danger, fishing, chat1


app = FastAPI(
    title="낚시 안전 API"
)


# =====================================================
# CSS / JavaScript 연결
# =====================================================

app.mount(
    "/static",
    StaticFiles(
        directory="src/kakaoapi/static"
    ),
    name="static"
)


# =====================================================
# Router 연결
# =====================================================

app.include_router(danger.router)

app.include_router(fishing.router)

app.include_router(chat1.router)


# =====================================================
# 메인 페이지
# =====================================================

@app.get("/")
async def root():

    return FileResponse(
        "src/kakaoapi/templates/location.html"
    )