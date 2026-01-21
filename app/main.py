# ai-gateway/app/main.py
# FASTAPI application 엔트리 포인트

from fastapi import FastAPI
from app.api.v1.routes import router as v1_router

def create_app() -> FastAPI:
    app = FastAPI(title="ai-gateway", version="0.1.0")
    app.include_router(v1_router, prefix="/v1")
    return app

app = create_app()
