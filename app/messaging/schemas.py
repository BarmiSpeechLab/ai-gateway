# ai-gateway/app/messaging/schemas.py
# RabbitMQ 메시지 스키마 정의 (파싱 및 검증)

from typing import Optional, Any
from pydantic import BaseModel, Field

class AudioJobMessage(BaseModel):
    """
    Backend에서 RabbitMQ를 통해 전달되는 음성 파일 처리 작업 메시지
    """
    file_path: str = Field(..., description="공유 볼륨의 음성 파일 경로", alias="filePath")
    
    class Config:
        json_schema_extra = {
            "example": {
                "file_path": "/shared/audio/sample.wav"
            }
        }
        populate_by_name = True  # 둘 다 받기 (filePath, file_path)

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
