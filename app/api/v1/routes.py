# ai-gateway/app/api/v1/routes.py
# FASTAPI 라우터 설정

from fastapi import APIRouter, HTTPException
import httpx

from app.api.v1.clients.ai_client import ai_healthcheck
from app.api.v1.health import router as health_router

router = APIRouter()

router.include_router(health_router, prefix="/health", tags=["health"])

# AI 서버 헬스 체크 프록시 엔드포인트
@router.get("/ai/health")
async def ai_health_proxy():
    try:
        return await ai_healthcheck()
    except httpx.RequestError:
        raise HTTPException(status_code=502, detail="AI server unreachable")
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=e.response.status_code, detail=e.response.text)