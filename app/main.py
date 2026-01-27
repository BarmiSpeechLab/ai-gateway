# ai-gateway/app/main.py
# FASTAPI application 엔트리 포인트

import threading
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from app.api.v1.routes import router as v1_router
from app.messaging.consumer import AudioJobConsumer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

consumer: AudioJobConsumer = None
consumer_thread: threading.Thread = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """FastAPI 앱 생명주기 관리 - startup/shutdown 이벤트"""
    global consumer, consumer_thread
    
    # Startup
    logger.info("FastAPI application starting...")
    
    try:
        consumer = AudioJobConsumer()
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

def create_app() -> FastAPI:
    app = FastAPI(
        title="ai-gateway",
        version="0.1.0",
        lifespan=lifespan
    )
    app.include_router(v1_router, prefix="/v1")
    return app

app = create_app()
