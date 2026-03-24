import uvicorn
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional
import tempfile
import os

from schemas import GradeRequest, GradeResponse
from models import grade_sync, grade_stream
from utils import extract_text_from_file

app = FastAPI(title="EduChat 作业批改 API")

# 跨域配置（允许前端开发环境访问）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # 生产环境应限制具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from fastapi import APIRouter

api_router = APIRouter(prefix="/api")

@api_router.post("/grade/sync", response_model=GradeResponse)
async def grade_sync_api(request: GradeRequest):
    """同步批改接口"""
    try:
        result = grade_sync(request.content, request.max_tokens)
        return GradeResponse(result=result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/grade/stream")
async def grade_stream_api(request: GradeRequest):
    """流式批改接口（Server-Sent Events）"""
    async def event_generator():
        try:
            for chunk in grade_stream(request.content, request.max_tokens):
                yield f"data: {chunk}\n\n"
        except Exception as e:
            yield f"data: [错误] {str(e)}\n\n"
    return StreamingResponse(event_generator(), media_type="text/event-stream")

@api_router.post("/grade/file")
async def grade_file(file: UploadFile = File(...), max_tokens: Optional[int] = 1024):
    """文件上传批改接口"""
    # 保存临时文件
    with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1]) as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = tmp.name

    try:
        text = extract_text_from_file(tmp_path)
        if text is None:
            raise HTTPException(status_code=400, detail="无法提取文件内容")
        result = grade_sync(text, max_tokens)
        return {"result": result}
    finally:
        os.unlink(tmp_path)  # 删除临时文件

@api_router.get("/health")
async def health():
    return {"status": "ok"}

from fastapi.staticfiles import StaticFiles
app.include_router(api_router)
app.mount("/", StaticFiles(directory="../frontend/dist", html=True), name="static")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)