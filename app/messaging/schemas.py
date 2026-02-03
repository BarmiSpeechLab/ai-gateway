# ai-gateway/app/messaging/schemas.py
# RabbitMQ 메시지 스키마 정의 (파싱 및 검증)

from typing import Optional, Any, List, Dict
from pydantic import BaseModel, Field

class AudioJobMessage(BaseModel):
    """
    Backend에서 RabbitMQ를 통해 전달되는 음성 파일 처리 작업 메시지
    """
    taskId: str = Field(..., alias="task_id")
    filePath: str = Field(..., alias="file_path")
    type: str = Field(..., description="ipa, conversation 등")
    analysisRequest: Dict[str, Any] = Field(..., alias="analysis_request")

    class Config:
        populate_by_name = True  # camelCase/snake_case 모두 허용

        json_schema_extra = {
            "example": {
                "taskId": "req_550e8400-e29b",
                "filePath": "/shared/audio/sample.wav",
                "type": "ipa",
                "analysisRequest": {
                    "fullText": "I like to dance",
                    "wordDetails": []
                }
            }
        }

class AudioResultMessage(BaseModel):
    """
    AI 서버 처리 결과를 Backend로 전달하는 메시지
    (type은 큐 선택에만 사용되고, payload에는 포함되지 않음)
    """
    taskId: str = Field(..., alias="task_id", description="작업 ID")
    status: str = Field(..., description="SUCCESS | FAIL")
    error: Optional[str] = Field(None, description="에러 메시지 (실패 시)")
    analysisResult: Optional[Any] = Field(None, alias="analysis_result", description="AI 분석 결과 데이터")
    
    class Config:
        populate_by_name = True  # camelCase/snake_case 모두 허용

        json_schema_extra = {
            "example": {
                "taskId": "req_20240127_001",
                "status": "SUCCESS",
                "error": None,
                "analysisResult": {"score": 85, "analysis": "..."}
            }
        }
