# ai-gateway/app/api/v1/health.py
# 헬스 체크 엔드포인트

from fastapi import APIRouter
from app.core.config import settings

router = APIRouter()

@router.get("")
def health():
    return {
        "status": "ok",
        "workers_configured": bool(settings.worker_urls),
    }
