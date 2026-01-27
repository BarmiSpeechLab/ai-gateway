# ai-gateway/app/messaging/producer.py
# RabbitMQ Producer - 결과를 result 큐에 발행

import json
import logging
import pika

from app.messaging.rabbitmq import RabbitMQConnection
from app.messaging.schemas import AudioResultMessage
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
        self.queue_name = settings.RABBITMQ_RESULT_QUEUE
    
    def connect(self):
        """RabbitMQ 연결"""
        self.rabbitmq.connect()
        logger.info(f"Producer connected to queue: {self.queue_name}")
    
    def publish_result(self, result_message: AudioResultMessage) -> bool:
        """
        처리 결과를 result 큐에 발행
        
        Args:
            result_message: 발행할 결과 메시지
        
        Returns:
            발행 성공 여부
        """
        try:
            if not self.rabbitmq.channel:
                self.connect()
            
            message_body = result_message.model_dump_json()
            
            self.rabbitmq.channel.basic_publish(
                exchange='',
                routing_key=self.queue_name,
                body=message_body,
                properties=pika.BasicProperties(
                    delivery_mode=2,  # 메시지 영속성
                    content_type='application/json'
                )
            )
            
            logger.info(f"Result published: {result_message.filePath}, success={result_message.success}")
            return True
        
        except Exception as e:
            logger.error(f"Failed to publish result: {e}")
            return False
    
    def close(self):
        """연결 종료"""
        self.rabbitmq.close()
