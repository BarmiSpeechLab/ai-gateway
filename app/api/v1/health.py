# ai-gateway/app/api/v1/health.py
# 헬스 체크 엔드포인트

from fastapi import APIRouter
from app.core.config import settings

router = APIRouter()

# 어플리케이션 서버 헬스 체크 엔드포인트
@router.get("")
def health():
    return {
        "status": "ok",
        "workers_configured": bool(settings.worker_urls_list),
    }
