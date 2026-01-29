# ai-gateway/app/main.py
# FASTAPI application 엔트리 포인트

import threading
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from app.api.v1.routes import router as v1_router
from app.messaging.consumer import AudioJobConsumer
from app.messaging.producer import AudioResultProducer
from app.api.v1.clients import ai_client
from app.services.file_service import FileService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

consumer: AudioJobConsumer = None
consumer_thread: threading.Thread = None
producer: AudioResultProducer = None
file_service: FileService = None


async def process_audio_job(file_path: str):
    """
    음성 파일 처리 orchestration 함수
    
    Args:
        file_path: 처리할 파일 경로
    """
    try:
        logger.info(f"파일 처리 시작: {file_path}")
        
        # 1. AI 서버로 분석 요청 및 결과 수신
        async for result in ai_client.analyze_audio(file_path):
            result_type = result.get("type")

            if result_type:
                producer.publish(
                    result_type=result_type,
                    data=result
                )
        
        # 3. 파일 삭제
        deleted = file_service.delete_file(file_path)
        if deleted:
            logger.info(f"파일 삭제 완료: {file_path}")
        else:
            logger.warning(f"파일 삭제 실패: {file_path}")
        
        logger.info(f"파일 처리 완료: {file_path}")
        
    except Exception as e:
        logger.error(f"파일 처리 실패: {file_path}, error: {e}")
        
        # 실패 결과 발행
        producer.publish(
            result_type="error",
            data={"error": str(e), "file_path": file_path}
        )

consumer: AudioJobConsumer = None
consumer_thread: threading.Thread = None
producer: AudioResultProducer = None
file_service: FileService = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """FastAPI 앱 생명주기 관리 - startup/shutdown 이벤트"""
    global consumer, consumer_thread, producer, file_service
    
    # Startup
    logger.info("FastAPI application starting...")
    
    try:
        # Producer 및 FileService 초기화
        producer = AudioResultProducer()
        file_service = FileService()
        
        # Consumer 초기화 (콜백 함수 전달)
        consumer = AudioJobConsumer(process_callback=process_audio_job)
        consumer_thread = threading.Thread(target=consumer.start, daemon=True)
        consumer_thread.start()
        logger.info("RabbitMQ consumer thread started")
    except Exception as e:
        logger.error(f"Failed to start consumer: {e}")
    
    yield
    
    # Shutdown
    logger.info("FastAPI application shutting down...")
    
    if consumer:
        try:
            consumer.stop()
            logger.info("Consumer stopped successfully")
        except Exception as e:
            logger.error(f"Failed to stop consumer: {e}")
    
    if producer:
        try:
            producer.close()
            logger.info("Producer closed successfully")
        except Exception as e:
            logger.error(f"Failed to close producer: {e}")

def create_app() -> FastAPI:
    app = FastAPI(
        title="ai-gateway",
        version="0.1.0",
        lifespan=lifespan
    )
    app.include_router(v1_router, prefix="/v1")
    return app

app = create_app()
