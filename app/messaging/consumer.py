# ai-gateway/app/messaging/consumer.py
# RabbitMQ Consumer - ai.jobs 큐에서 메시지만 수신

import json
import logging
import asyncio
import threading
import pika

from app.messaging.rabbitmq import RabbitMQConnection
from app.messaging.schemas import AudioJobMessage
from app.core.config import settings

logger = logging.getLogger(__name__)

class AudioJobConsumer:
    """
    ai.jobs 큐에서 음성 파일 처리 작업 메시지를 수신하는 Consumer
    메시지 수신만 담당하고, 실제 처리는 콜백 함수에 위임
    """
    
    def __init__(self, process_callback=None):
        self.rabbitmq = RabbitMQConnection(
            host=settings.RABBITMQ_HOST,
            port=settings.RABBITMQ_PORT,
            username=settings.RABBITMQ_USER,
            password=settings.RABBITMQ_PASS,
            vhost=settings.RABBITMQ_VHOST
        )
        self.queue_name = settings.RABBITMQ_JOB_QUEUE
        self.process_callback = process_callback
    
    def start(self):
        """
        Consumer 시작 - RabbitMQ 연결 후 메시지 수신 대기
        """
        try:
            # RabbitMQ 연결
            self.rabbitmq.connect()
            
            # Consumer 등록
            self.rabbitmq.channel.basic_qos(prefetch_count=5)  # 5개 동시 처리
            self.rabbitmq.channel.basic_consume(
                queue=self.queue_name,
                on_message_callback=self._on_message,
                auto_ack=False  # 수동 ACK
            )
            
            logger.info(f"Consumer 시작: {self.queue_name} 큐에서 메시지 대기 중...")
            self.rabbitmq.channel.start_consuming()
            
        except KeyboardInterrupt:
            logger.info("Consumer 중단 요청")
            self.stop()
        except Exception as e:
            logger.error(f"Consumer 에러: {e}")
            raise
    
    def _on_message(self, channel, method, properties, body):
        """
        메시지 수신 시 호출되는 콜백 함수
        백그라운드 스레드에서 비동기 처리 시작 후 즉시 ACK
        """
        task_id = None
        try:
            # 1. 메시지 파싱
            message_dict = json.loads(body)
            task_id = message_dict.get("taskId") or message_dict.get("task_id")
            message = AudioJobMessage(**message_dict)
            file_path = message.filePath
            logger.info(f"메시지 수신: {file_path}")
            
            # 2. 백그라운드 스레드에서 처리 시작
            if self.process_callback:
                threading.Thread(
                    target=self._process_in_thread,
                    args=(file_path, message.taskId, message.analysisRequest),
                    daemon=True
                ).start()
            else:
                logger.warning("처리 콜백이 정의되지 않음")
                channel.basic_nack(delivery_tag=method.delivery_tag, requeue=True)
                return
            
            # 3. 즉시 ACK (처리를 기다리지 않음)
            channel.basic_ack(delivery_tag=method.delivery_tag)
            logger.info(f"메시지 수신 완료: {file_path}")
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON 파싱 에러: {e}")
            channel.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
            # taskId 추출 실패 시 에러 발행 불가
            if task_id:
                self._publish_parse_error(task_id, str(e))
        except Exception as e:
            logger.error(f"메시지 처리 에러: {e}")
            channel.basic_nack(delivery_tag=method.delivery_tag, requeue=True)
            # Pydantic 검증 실패 등의 경우에도 에러 발행 시도
            if task_id:
                self._publish_parse_error(task_id, str(e))
    
    def _process_in_thread(self, file_path: str, task_id: str, analysis_request: dict):
        """
        스레드에서 실행되는 비동기 처리
        """
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(self.process_callback(file_path, task_id, analysis_request))
        finally:
            loop.close()
    
    def _publish_parse_error(self, task_id: str, error_msg: str):
        """
        메시지 파싱 에러를 모든 타입 큐로 발행
        """
        from app.messaging.producer import AudioResultProducer
        
        error_message = {
            "taskId": task_id,
            "status": "FAIL",
            "error": f"MESSAGE_PARSE_ERROR: {error_msg}",
            "analysisResult": None
        }
        
        try:
            producer = AudioResultProducer()
            for result_type in ["pron", "inton", "llm"]:
                producer.publish(result_type=result_type, data=error_message)
            producer.close()
        except Exception as e:
            logger.error(f"파싱 에러 발행 실패: {e}")
    
    def stop(self):
        """
        Consumer 중지
        """
        try:
            if self.rabbitmq.channel and self.rabbitmq.channel.is_open:
                self.rabbitmq.channel.stop_consuming()
            self.rabbitmq.close()
            logger.info("Consumer 종료 완료")
        except Exception as e:
            logger.error(f"Consumer 종료 에러: {e}")
