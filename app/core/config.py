# ai-gateway/app/core/config.py
# 애플리케이션 환경 설정

import os
from pydantic import BaseModel

class Settings(BaseModel):
    worker_urls: list[str] = []

def _parse_urls(raw: str) -> list[str]:
    raw = raw.strip()
    if not raw:
        return []
    return [u.strip().rstrip("/") for u in raw.split(",") if u.strip()]

settings = Settings(
    worker_urls=_parse_urls(os.getenv("WORKER_URLS", "")),
)