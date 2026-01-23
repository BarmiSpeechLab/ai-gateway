# ai-gateway/app/core/config.py
# 애플리케이션 환경 설정

import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    AI_BASE_URL: str = "http://localhost:5000" # AI 서버 기본 URL
    AI_TIMEOUT_SEC: int = 100 # AI 서버 요청 타임아웃 (초)

    WORKER_URLS: str = "" # 콤마로 구분된 워커 URL 목록
    
    @property
    def worker_urls_list(self) -> list[str]:
        return _parse_urls(self.WORKER_URLS)
    
    class Config:
        env_file = ".env"
        case_sensitive = False

# 유틸리티 함수: 콤마로 구분된 URL 문자열을 리스트로 변환
def _parse_urls(raw: str) -> list[str]:
    raw = raw.strip()
    if not raw:
        return []
    return [u.strip().rstrip("/") for u in raw.split(",") if u.strip()]

settings = Settings()