# ai-gateway/app/messaging/consumer.py
# RabbitMQ Consumer - ai.jobs 큐에서 메시지를 받아 처리

import json
import logging
from typing import Callable
import pika

from app.messaging.rabbitmq import RabbitMQConnection
from app.messaging.schemas import AudioJobMessage, AudioResultMessage
from app.messaging.producer import AudioResultProducer
from app.services.file_service import FileService
from app.core.config import settings

logger = logging.getLogger(__name__)

class AudioJobConsumer:
    """
    ai.jobs 큐에서 음성 파일 처리 작업을 수신하는 Consumer
    """
    
    def __init__(self):
        self.rabbitmq = RabbitMQConnection(
            host=settings.RABBITMQ_HOST,
            port=settings.RABBITMQ_PORT,
            username=settings.RABBITMQ_USER,
            password=settings.RABBITMQ_PASS,
            vhost=settings.RABBITMQ_VHOST
        )
        self.queue_name = settings.RABBITMQ_QUEUE
        self.file_service = FileService()
        self.result_producer = AudioResultProducer()
    
    def start(self):
        """
        Consumer 시작 - RabbitMQ 연결 후 메시지 수신 대기
        """
        try:
            # RabbitMQ 연결
            self.rabbitmq.connect()
            
            # Consumer 등록
            self.rabbitmq.channel.basic_qos(prefetch_count=1)  # 한 번에 하나씩 처리
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
            logger.error(f"❌ Consumer 에러: {e}")
            raise
    
    def _on_message(self, channel, method, properties, body):
        """
        메시지 수신 시 호출되는 콜백 함수
        
        Args:
            channel: RabbitMQ 채널
            method: 메시지 메타데이터
            properties: 메시지 속성
            body: 메시지 본문 (JSON)
        """
        try:
            # 1. 메시지 파싱
            message_dict = json.loads(body)
            message = AudioJobMessage(**message_dict)
            logger.info(f"메시지 수신: {message.filePath}")
            
            # 2. 파일 처리
            self._process_audio_file(message.filePath)
            
            # 3. ACK (처리 완료)
            channel.basic_ack(delivery_tag=method.delivery_tag)
            logger.info(f"✅ 메시지 처리 완료: {message.filePath}")
            
        except json.JSONDecodeError as e:
            logger.error(f"❌ JSON 파싱 에러: {e}")
            channel.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
        
        except FileNotFoundError as e:
            logger.error(f"❌ 파일 없음: {e}")
            channel.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
        
        except Exception as e:
            logger.error(f"❌ 메시지 처리 에러: {e}")
            # 재시도를 위해 requeue=True
            channel.basic_nack(delivery_tag=method.delivery_tag, requeue=True)
    
    def _process_audio_file(self, file_path: str):
        """
        음성 파일 처리 로직
        
        Args:
            file_path: 처리할 파일 경로
        """
        result_message = None
        
        try:
            # 1. 파일 정보 조회
            file_info = self.file_service.get_file_info(file_path)
            logger.info(f"File info: {file_info}")
            
            # 2. 파일 읽기
            audio_data = self.file_service.read_file(file_path)
            logger.info(f"File read complete: {len(audio_data)} bytes")
            
            # 3. TODO: AI 서버로 전송하여 분석
            # ai_result = await ai_client.analyze(audio_data)
            logger.info(f"[TODO] Send to AI server: {file_path}")
            ai_result = {"status": "pending", "message": "AI processing not implemented yet"}
            
            # 4. 성공 결과 메시지 생성
            result_message = AudioResultMessage(
                filePath=file_path,
                success=True,
                result=ai_result,
                error=None
            )
            
            # 5. 파일 삭제
            deleted = self.file_service.delete_file(file_path)
            if deleted:
                logger.info(f"File deleted: {file_path}")
            else:
                logger.warning(f"File deletion failed: {file_path}")
        
        except Exception as e:
            logger.error(f"File processing failed: {file_path}, error: {e}")
            
            # 실패 결과 메시지 생성
            result_message = AudioResultMessage(
                filePath=file_path,
                success=False,
                result=None,
                error=str(e)
            )
            raise
        
        finally:
            # 6. 결과를 RabbitMQ result 큐에 발행
            if result_message:
                try:
                    self.result_producer.publish_result(result_message)
                except Exception as e:
                    logger.error(f"Failed to publish result: {e}")
    
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
            logger.error(f"❌ Consumer 종료 에러: {e}")
