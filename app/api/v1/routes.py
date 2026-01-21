# ai-gateway/app/api/v1/routes.py
# FASTAPI 라우터 설정

from fastapi import APIRouter
from app.api.v1.health import router as health_router

router = APIRouter()
router.include_router(health_router, prefix="/health", tags=["health"])