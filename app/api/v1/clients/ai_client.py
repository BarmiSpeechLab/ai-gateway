# ai-gateway/app/api/v1/clients/ai_client.py
# HTTP GET/POST 요청을 AI 서버의 엔드포인트로 전달

import httpx
from app.core.config import settings

# AI 서버 헬스 체크 요청 프록시 함수
async def ai_healthcheck():
    async with httpx.AsyncClient(timeout=settings.AI_TIMEOUT_SEC) as client:
        r = await client.get(f"{settings.AI_BASE_URL}/health")
        r.raise_for_status()
        return r.json()

# AI 서버 출력 요청 프록시 함수
async def ai_output(payload: dict):
    async with httpx.AsyncClient(timeout=settings.AI_TIMEOUT_SEC) as client:
        r = await client.post(
            f"{settings.AI_BASE_URL}/output",
            json=payload
        )
        r.raise_for_status()
        return r.json()
