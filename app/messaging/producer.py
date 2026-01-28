# ai-gateway/app/messaging/producer.py
# RabbitMQ Producer - 결과를 result 큐에 발행

import json
import logging
import pika

from app.messaging.rabbitmq import RabbitMQConnection
from app.core.config import settings

logger = logging.getLogger(__name__)


class AudioResultProducer:
    """
    AI 처리 결과를 RabbitMQ result 큐에 발행하는 Producer
    """
    
    def __init__(self):
        self.rabbitmq = RabbitMQConnection(
            host=settings.RABBITMQ_HOST,
            port=settings.RABBITMQ_PORT,
            username=settings.RABBITMQ_USER,
            password=settings.RABBITMQ_PASS,
            vhost=settings.RABBITMQ_VHOST
        )
        self._connected = False
    
    def connect(self):
        """RabbitMQ 연결"""
        if not self._connected:
            self.rabbitmq.connect()
            self._connected = True
            logger.info("Producer connected")
    
    def publish(self, result_type: str, data: dict):
        """
        Type별로 다른 큐에 발행 (스트리밍 결과용)
        
        Args:
            result_type: 결과 타입 (pron, inton, feedback, llm)
            data: AI 분석 결과 데이터
        """
        # type별 큐 매핑
        queue_map = {
            "pron": "pron_result",
            "inton": "inton_result",
            "llm": "llm_result",
        }
        
        queue_name = queue_map.get(result_type, f"{result_type}_result")
        
        try:
            self.connect()
            
            message = {
                "type": result_type,
                "data": data
            }
            
            message_body = json.dumps(message, ensure_ascii=False)
            
            self.rabbitmq.channel.basic_publish(
                exchange='',
                routing_key=queue_name,
                body=message_body,
                properties=pika.BasicProperties(
                    delivery_mode=2,
                    content_type='application/json'
                )
            )
            
            logger.info(f"Result published to {queue_name}, type={result_type}")
        
        except Exception as e:
            logger.error(f"Failed to publish result: {e}")
            raise

    def close(self):
        """연결 종료"""
        if self._connected:
            self.rabbitmq.close()
            self._connected = False
