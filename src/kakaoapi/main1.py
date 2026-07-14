from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .routers import danger, fishing


app = FastAPI(
    title="낚시 안전 API"
)


# CSS / JavaScript 파일 연결
app.mount(
    "/static",
    StaticFiles(directory="src/kakaoapi/static"),
    name="static"
)


# 라우터 연결
app.include_router(danger.router)
app.include_router(fishing.router)


# 메인 화면
@app.get("/")
async def root():

    return FileResponse(
        "src/kakaoapi/templates/location.html"
    )