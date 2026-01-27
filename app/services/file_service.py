# ai-gateway/app/services/file_service.py
# 공유 볼륨의 파일 처리 서비스

import logging
from pathlib import Path

logger = logging.getLogger(__name__)

class FileService:
    """
    공유 볼륨의 음성 파일을 처리하는 서비스
    - 파일 읽기
    - 파일 존재 확인
    - 파일 삭제
    """
    
    @staticmethod
    def read_file(file_path: str) -> bytes:
        """
        파일을 읽어서 바이트 데이터로 반환
        
        Args:
            file_path: 읽을 파일의 경로 (예: /shared/audio/sample.wav)
        
        Returns:
            파일의 바이트 데이터
        
        Raises:
            FileNotFoundError: 파일이 존재하지 않을 때
            IOError: 파일 읽기 실패 시
        """
        path = Path(file_path)
        
        if not path.exists():
            logger.error(f"파일을 찾을 수 없음: {file_path}")
            raise FileNotFoundError(f"파일이 존재하지 않습니다: {file_path}")
        
        if not path.is_file():
            logger.error(f"파일이 아님: {file_path}")
            raise IOError(f"유효한 파일이 아닙니다: {file_path}")
        
        try:
            with open(path, 'rb') as f:
                data = f.read()
            
            file_size = len(data)
            logger.info(f"파일 읽기 성공: {file_path} ({file_size} bytes)")
            return data
        
        except Exception as e:
            logger.error(f"파일 읽기 실패: {file_path}, 에러: {e}")
            raise IOError(f"파일 읽기 실패: {e}")
    
    @staticmethod
    def delete_file(file_path: str) -> bool:
        """
        파일 삭제
        
        Args:
            file_path: 삭제할 파일의 경로
        
        Returns:
            삭제 성공 여부
        """
        path = Path(file_path)
        
        if not path.exists():
            logger.warning(f"삭제할 파일이 없음: {file_path}")
            return False
        
        try:
            path.unlink()
            logger.info(f"파일 삭제 완료: {file_path}")
            return True
        
        except Exception as e:
            logger.error(f"파일 삭제 실패: {file_path}, 에러: {e}")
            return False
    
    @staticmethod
    def get_file_info(file_path: str) -> dict:
        """
        파일 정보 조회 (디버깅/로깅용)
        
        Args:
            file_path: 파일 경로
        
        Returns:
            파일 정보 딕셔너리 (이름, 크기, 확장자 등)
        """
        path = Path(file_path)
        
        if not path.exists():
            return {"exists": False, "path": file_path}
        
        stat = path.stat()
        return {
            "exists": True,
            "path": str(path),
            "name": path.name,
            "size": stat.st_size,
            "extension": path.suffix,
            "is_file": path.is_file()
        }
