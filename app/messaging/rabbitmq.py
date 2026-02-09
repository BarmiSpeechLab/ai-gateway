import logging
from typing import Optional

import pika

logger = logging.getLogger(__name__)


class RabbitMQConnection:
    def __init__(
        self,
        host: str,
        port: int,
        username: str,
        password: str,
        vhost: str,
        heartbeat_sec: int = 180,
        blocked_connection_timeout_sec: int = 60,
        connection_attempts: int = 5,
        retry_delay_sec: int = 3,
        socket_timeout_sec: int = 10,
    ):
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.vhost = vhost
        self.heartbeat_sec = heartbeat_sec
        self.blocked_connection_timeout_sec = blocked_connection_timeout_sec
        self.connection_attempts = connection_attempts
        self.retry_delay_sec = retry_delay_sec
        self.socket_timeout_sec = socket_timeout_sec
        self.connection: Optional[pika.BlockingConnection] = None
        self.channel: Optional[pika.channel.Channel] = None

    def connect(self):
        credentials = pika.PlainCredentials(self.username, self.password)
        parameters = pika.ConnectionParameters(
            host=self.host,
            port=self.port,
            virtual_host=self.vhost,
            credentials=credentials,
            heartbeat=self.heartbeat_sec,
            blocked_connection_timeout=self.blocked_connection_timeout_sec,
            connection_attempts=self.connection_attempts,
            retry_delay=self.retry_delay_sec,
            socket_timeout=self.socket_timeout_sec,
        )
        self.connection = pika.BlockingConnection(parameters)
        self.channel = self.connection.channel()
        logger.info("RabbitMQ connected: %s:%s", self.host, self.port)

    def close(self):
        if self.connection and not self.connection.is_closed:
            self.connection.close()
            logger.info("RabbitMQ connection closed")
        self.connection = None
        self.channel = None
