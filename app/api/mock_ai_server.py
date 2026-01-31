# Mock AI Server for testing ai-gateway
# Usage: python mock_ai_server.py

import json
import logging
from fastapi import FastAPI, File, UploadFile, Form
from fastapi.responses import StreamingResponse
import uvicorn

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Mock AI Server")

@app.get("/health")
async def health():
    """헬스 체크"""
    return {"status": "ok"}

@app.post("/analyze")
async def analyze(
    file: UploadFile = File(...),
    taskId: str = Form(...),
    analysisRequest: str = Form(...)
):
    """
    Mock AI 분석 엔드포인트
    스트리밍 응답 (NDJSON 형식)
    """
    logger.info(f"분석 요청: taskId={taskId}, file={file.filename}")
    
    # analysisRequest 파싱
    try:
        analysis_req = json.loads(analysisRequest)
        full_text = analysis_req.get("fullText", "")
    except:
        full_text = ""
    
    async def generate():
        """스트리밍 응답 생성"""
        
        # 1. 발음(pron) 분석 결과
        pron_result = {
            "type": "pron",
            "taskId": taskId,
            "status": "SUCCESS",
            "error": None,
            "analysisResult": {
                "score": 85,
                "words": [
                    {
                        "word": "hello",
                        "accuracy": 0.92,
                        "phonemes": [
                            {"cpl": "H", "cipa": "h", "score": 0.95},
                            {"cpl": "AE", "cipa": "æ", "score": 0.88},
                        ]
                    }
                ]
            }
        }
        yield json.dumps(pron_result, ensure_ascii=False) + "\n"
        logger.info(f"Sent pron result for {taskId}")
        
        # 2. 인토네이션(inton) 분석 결과
        inton_result = {
            "type": "inton",
            "taskId": taskId,
            "status": "SUCCESS",
            "error": None,
            "analysisResult": {
                "score": 78,
                "pitch_curve": [100, 105, 110, 108, 102],
                "duration_analysis": {
                    "total_duration": 2.5,
                    "pause_count": 1
                }
            }
        }
        yield json.dumps(inton_result, ensure_ascii=False) + "\n"
        logger.info(f"Sent inton result for {taskId}")
        
        # 3. LLM 피드백 결과
        llm_result = {
            "type": "llm",
            "taskId": taskId,
            "status": "SUCCESS",
            "error": None,
            "analysisResult": {
                "feedback": "Your pronunciation is good overall. Try to speak more slowly.",
                "suggestions": [
                    {"issue": "speed", "recommendation": "Reduce speaking speed"},
                    {"issue": "clarity", "recommendation": "Articulate consonants more clearly"}
                ]
            }
        }
        yield json.dumps(llm_result, ensure_ascii=False) + "\n"
        logger.info(f"Sent llm result for {taskId}")
    
    return StreamingResponse(generate(), media_type="application/x-ndjson")


if __name__ == "__main__":
    logger.info("Starting Mock AI Server on http://localhost:5001")
    uvicorn.run(app, host="0.0.0.0", port=5001)
