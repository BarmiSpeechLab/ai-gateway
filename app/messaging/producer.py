import json
import logging

import pika

from app.core.config import settings
from app.messaging.rabbitmq import RabbitMQConnection

logger = logging.getLogger(__name__)


class AudioResultProducer:
    def __init__(self):
        self.rabbitmq = RabbitMQConnection(
            host=settings.RABBITMQ_HOST,
            port=settings.RABBITMQ_PORT,
            username=settings.RABBITMQ_USER,
            password=settings.RABBITMQ_PASS,
            vhost=settings.RABBITMQ_VHOST,
            heartbeat_sec=settings.RABBITMQ_HEARTBEAT_SEC,
            blocked_connection_timeout_sec=settings.RABBITMQ_BLOCKED_CONNECTION_TIMEOUT_SEC,
            connection_attempts=settings.RABBITMQ_CONNECTION_ATTEMPTS,
            retry_delay_sec=settings.RABBITMQ_RETRY_DELAY_SEC,
            socket_timeout_sec=settings.RABBITMQ_SOCKET_TIMEOUT_SEC,
        )
        self._connected = False

    def connect(self):
        if (
            not self._connected
            or not self.rabbitmq.connection
            or self.rabbitmq.connection.is_closed
            or not self.rabbitmq.channel
            or self.rabbitmq.channel.is_closed
        ):
            self.rabbitmq.connect()
            self._connected = True
            logger.info("Producer connected")

    def publish(self, result_type: str, data: dict):
        queue_map = {
            "pron": settings.RABBITMQ_PRON_QUEUE,
            "inton": settings.RABBITMQ_INTON_QUEUE,
            "llm": settings.RABBITMQ_LLM_QUEUE,
            "error": settings.RABBITMQ_ERROR_QUEUE,
            "conversation": settings.RABBITMQ_CONVERSATION_QUEUE,
        }
        queue_name = queue_map.get(result_type, f"{result_type}_result")

        if isinstance(data, dict) and "type" in data:
            payload = {k: v for k, v in data.items() if k != "type"}
        else:
            payload = data
        message_body = json.dumps(payload, ensure_ascii=False)

        try:
            self.connect()
            self.rabbitmq.channel.basic_publish(
                exchange="",
                routing_key=queue_name,
                body=message_body,
                properties=pika.BasicProperties(
                    delivery_mode=2,
                    content_type="application/json",
                ),
            )
            logger.info("Result published to %s, type=%s", queue_name, result_type)
        except Exception as e:
            logger.warning("Publish failed, retrying once after reconnect: %s", e)
            self._connected = False
            self.rabbitmq.close()
            self.connect()
            self.rabbitmq.channel.basic_publish(
                exchange="",
                routing_key=queue_name,
                body=message_body,
                properties=pika.BasicProperties(
                    delivery_mode=2,
                    content_type="application/json",
                ),
            )
            logger.info("Result published after reconnect to %s, type=%s", queue_name, result_type)

    def close(self):
        try:
            if self._connected and self.rabbitmq:
                self.rabbitmq.close()
                self._connected = False
                logger.info("Producer closed successfully")
        except Exception as e:
            logger.error("Failed to close producer: %s", e)
