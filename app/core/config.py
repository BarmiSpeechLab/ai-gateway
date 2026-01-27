# ai-gateway/app/core/config.py
# 애플리케이션 환경 설정

import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    AI_BASE_URL: str = "http://localhost:5000" # AI 서버 기본 URL
    AI_TIMEOUT_SEC: int = 100 # AI 서버 요청 타임아웃 (초)

    WORKER_URLS: str = "" # 콤마로 구분된 워커 URL 목록
    
    # RabbitMQ 설정
    RABBITMQ_HOST: str  # .env
    RABBITMQ_PORT: int = 5672
    RABBITMQ_USER: str  # .env
    RABBITMQ_PASS: str  # .env
    RABBITMQ_VHOST: str = "/barmi"
    RABBITMQ_QUEUE: str = "ai.jobs"  # Consumer가 수신하는 큐
    RABBITMQ_RESULT_QUEUE: str = "ai.results"  # Producer가 발행하는 결과 큐
    
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