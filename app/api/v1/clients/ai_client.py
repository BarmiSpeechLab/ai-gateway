# ai-gateway/app/api/v1/clients/ai_client.py
# HTTP GET/POST 요청을 AI 서버의 엔드포인트로 전달

import json
import logging
import httpx
from app.core.config import settings
from app.services.file_service import FileService

logger = logging.getLogger(__name__)
file_service = FileService()

# AI 서버 헬스 체크 요청 프록시 함수
async def ai_healthcheck():
    async with httpx.AsyncClient(timeout=settings.AI_TIMEOUT_SEC) as client:
        r = await client.get(f"{settings.AI_BASE_URL}/health")
        r.raise_for_status()
        return r.json()


# AI 서버 음성 파일 분석 함수
async def analyze_audio(file_path: str, task_id: str, script_info: dict):
    """
    음성 파일을 AI 서버로 전송하여 분석
    스트리밍 방식 - AI 서버 결과를 한 줄씩 yield
    
    Args:
        file_path: 분석할 음성 파일 경로 (/shared/audio/xxx.wav)
        task_id: 작업 ID
        script_info: 스크립트 정보
    
    Returns:
        AI 서버 분석 결과 (score, feedback, etc.)
    """
    try:
        # 1. 파일 읽기
        logger.info(f"파일 읽기 시작: {file_path}")
        audio_data = file_service.read_file(file_path) # bytes로 변환
        logger.debug(f"파일 읽기 완료: {len(audio_data)} bytes")
        
        # 2. AI 서버에 전송
        files = {
            "file": ("audio.wav", audio_data, "audio/wav")
        }
        data = {
            "taskId": task_id,
            "scriptInfo": json.dumps(script_info, ensure_ascii=False)
        }
        
        logger.info(f"AI 서버 요청 시작: {file_path}")
        
        async with httpx.AsyncClient(timeout=300.0) as client:
            response = await client.post(
                f"{settings.AI_BASE_URL}/analyze",
                files=files,
                data=data
            )
            response.raise_for_status()

            async for line in response.aiter_lines():
                if line:
                    data = json.loads(line)
                    # type별로 분기해서 yield
                    yield data
                    
        logger.info(f"AI 서버 요청 완료: {file_path}")

    except FileNotFoundError as e:
        logger.error(f"파일 없음: {file_path}")
        raise
    except httpx.TimeoutException:
        logger.error(f"AI 서버 타임아웃: {file_path}")
        raise Exception("AI 서버 응답 타임아웃")
    except httpx.HTTPStatusError as e:
        logger.error(f"AI 서버 HTTP 에러: {file_path}, status: {e.response.status_code}")
        raise Exception(f"AI 서버 에러: {e.response.status_code}")
    except Exception as e:
        logger.error(f"AI 서버 통신 실패: {file_path}, error: {e}")
        raise