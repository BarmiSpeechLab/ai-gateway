# ai-gateway/app/messaging/rabbitmq.py
# RabbitMQ 연결 관리

import pika
import logging
from typing import Optional

logger = logging.getLogger(__name__)

class RabbitMQConnection:
    """
    RabbitMQ 연결과 채널을 관리하는 클래스
    """
    def __init__(self, host: str, port: int, username: str, password: str, vhost: str):
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.vhost = vhost
        self.connection: Optional[pika.BlockingConnection] = None
        self.channel: Optional[pika.channel.Channel] = None
    
    def connect(self):
        """RabbitMQ 서버에 연결"""
        try:
            credentials = pika.PlainCredentials(self.username, self.password)
            parameters = pika.ConnectionParameters(
                host=self.host,
                port=self.port,
                virtual_host=self.vhost,
                credentials=credentials,
                heartbeat=600,
                blocked_connection_timeout=300
            )
            self.connection = pika.BlockingConnection(parameters)
            self.channel = self.connection.channel()
            logger.info(f"✅ RabbitMQ 연결 성공: {self.host}:{self.port}")
        except Exception as e:
            logger.error(f"❌ RabbitMQ 연결 실패: {e}")
            raise
    
    def close(self):
        """연결 종료"""
        if self.connection and not self.connection.is_closed:
            self.connection.close()
            logger.info("RabbitMQ 연결 종료")
