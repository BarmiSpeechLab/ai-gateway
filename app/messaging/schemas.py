# ai-gateway/app/messaging/schemas.py
# RabbitMQ 메시지 스키마 정의 (파싱 및 검증)

from typing import Optional, Any, List, Dict
from pydantic import BaseModel, Field

class AudioJobMessage(BaseModel):
    """
    Backend에서 RabbitMQ를 통해 전달되는 음성 파일 처리 작업 메시지
    """
    taskId: str = Field(..., alias="task_id")
    audioInfo: Dict[str, str] = Field(..., alias="audio_info")
    scriptInfo: Dict[str, Any] = Field(..., alias="script_info")
    class Config:
        populate_by_name = True  # camelCase/snake_case 모두 허용

        json_schema_extra = {
            "example": {
                "taskId": "req_550e8400-e29b",
                "audioInfo": {"filePath": "/shared/audio/sample.wav"},
                "scriptInfo": {"fullText": "I like to dance"}
            }
        }

class AudioResultMessage(BaseModel):
    """
    AI 서버 처리 결과를 Backend로 전달하는 메시지
    """
    filePath: str = Field(..., description="처리된 파일 경로")
    success: bool = Field(..., description="처리 성공 여부")
    result: Optional[Any] = Field(None, description="AI 분석 결과 데이터")
    error: Optional[str] = Field(None, description="에러 메시지 (실패 시)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "filePath": "/shared/audio/sample.wav",
                "success": True,
                "result": {"score": 85, "analysis": "..."},
                "error": None
            }
        }
