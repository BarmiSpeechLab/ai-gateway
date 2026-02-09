import asyncio
import json
import logging
import threading
import time
from typing import Optional

from app.core.config import settings
from app.messaging.rabbitmq import RabbitMQConnection
from app.messaging.schemas import AudioJobMessage

logger = logging.getLogger(__name__)


class BaseJobConsumer:
    def __init__(self, queue_name: str, process_callback=None):
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
        self.queue_name = queue_name
        self.process_callback = process_callback
        self._stop_requested = False

    def start(self):
        reconnect_delay = settings.RABBITMQ_RECONNECT_INITIAL_DELAY_SEC
        max_reconnect_delay = settings.RABBITMQ_RECONNECT_MAX_DELAY_SEC

        while not self._stop_requested:
            try:
                self.rabbitmq.connect()
                self.rabbitmq.channel.basic_qos(prefetch_count=5)
                self.rabbitmq.channel.basic_consume(
                    queue=self.queue_name,
                    on_message_callback=self._on_message,
                    auto_ack=False,
                )
                logger.info("Consumer started: queue=%s", self.queue_name)
                reconnect_delay = settings.RABBITMQ_RECONNECT_INITIAL_DELAY_SEC
                self.rabbitmq.channel.start_consuming()
            except KeyboardInterrupt:
                logger.info("Consumer stop requested by keyboard interrupt")
                self.stop()
            except Exception as e:
                if self._stop_requested:
                    break
                logger.error("Consumer connection error (queue=%s): %s", self.queue_name, e)
                logger.info("Reconnecting queue=%s in %ss", self.queue_name, reconnect_delay)
                time.sleep(reconnect_delay)
                reconnect_delay = min(reconnect_delay * 2, max_reconnect_delay)
            finally:
                self.rabbitmq.close()

    def _on_message(self, channel, method, properties, body):
        task_id: Optional[str] = None
        try:
            message_dict = json.loads(body)
            task_id = message_dict.get("taskId") or message_dict.get("task_id")
            message = AudioJobMessage(**message_dict)
            file_path = message.filePath
            logger.info("Message received: queue=%s file=%s", self.queue_name, file_path)

            if self.process_callback:
                threading.Thread(
                    target=self._process_in_thread,
                    args=(file_path, message.taskId, message.analysisRequest),
                    daemon=True,
                ).start()
            else:
                logger.warning("Process callback is not configured")
                channel.basic_nack(delivery_tag=method.delivery_tag, requeue=True)
                return

            channel.basic_ack(delivery_tag=method.delivery_tag)
            logger.info("Message acked: queue=%s task_id=%s", self.queue_name, message.taskId)

        except json.JSONDecodeError as e:
            logger.error("JSON parse error: %s", e)
            channel.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
            if task_id:
                self._publish_parse_error(task_id, str(e))
        except Exception as e:
            logger.error("Message handling error: %s", e)
            channel.basic_nack(delivery_tag=method.delivery_tag, requeue=True)
            if task_id:
                self._publish_parse_error(task_id, str(e))

    def _process_in_thread(self, file_path: str, task_id: str, analysis_request: dict):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(self.process_callback(file_path, task_id, analysis_request))
        finally:
            loop.close()

    def _publish_parse_error(self, task_id: str, error_msg: str):
        from app.messaging.producer import AudioResultProducer

        error_message = {
            "taskId": task_id,
            "status": "FAIL",
            "error": f"MESSAGE_PARSE_ERROR: {error_msg}",
            "analysisResult": None,
        }

        try:
            producer = AudioResultProducer()
            producer.publish(result_type="error", data=error_message)
            producer.close()
        except Exception as e:
            logger.error("Failed to publish parse error message: %s", e)

    def stop(self):
        try:
            self._stop_requested = True
            if (
                self.rabbitmq.connection
                and self.rabbitmq.connection.is_open
                and self.rabbitmq.channel
                and self.rabbitmq.channel.is_open
            ):
                self.rabbitmq.connection.add_callback_threadsafe(
                    self.rabbitmq.channel.stop_consuming
                )
            self.rabbitmq.close()
            logger.info("Consumer stopped: queue=%s", self.queue_name)
        except Exception as e:
            logger.error("Consumer stop error: %s", e)


class AudioJobConsumer(BaseJobConsumer):
    def __init__(self, process_callback=None):
        super().__init__(settings.RABBITMQ_JOB_QUEUE, process_callback)


class ConversationJobConsumer(BaseJobConsumer):
    def __init__(self, process_callback=None):
        super().__init__(settings.RABBITMQ_CONVERSATION_JOB_QUEUE, process_callback)
