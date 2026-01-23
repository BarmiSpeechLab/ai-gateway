# ai-gateway
AI 백엔드(FastAPI) 레포지토리입니다.

### 🔄 요청 흐름도
```
클라이언트 (frontend/backend)
    ↓
ai-gateway:8000 (FastAPI)
    ↓
[main.py] FastAPI 앱 생성
    ↓
[routes.py] 라우팅 처리 (/v1/ai/health 또는 /v1/ai/output)
    ↓
[ai_client.py] httpx로 실제 AI 서버에 요청
    ↓
AI 서버 (실제 분석 수행)
    ↓
[ai_client.py] 응답 받아서 JSON 반환
    ↓
[routes.py] 에러 핸들링 후 반환
    ↓
클라이언트로 최종 응답
```