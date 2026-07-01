import uvicorn
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional, List
import tempfile
import os

from schemas import GradeRequest, GradeResponse
from models import grade_sync, grade_stream
from utils import extract_text_from_file
from analytics import analytics_engine
from rubric import rubric_engine

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

# ==================== 数据分析API ====================

from typing import List, Dict, Any

class BatchGradeRequest(BaseModel):
    """批量批改请求"""
    submissions: List[Dict[str, Any]]
    subject: Optional[str] = "math"

@api_router.post("/analytics/batch-grade")
async def batch_grade_api(request: BatchGradeRequest):
    """批量批改作业并生成分析报告"""
    try:
        result = analytics_engine.batch_grade(request.submissions, request.subject)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/analytics/generate-sample/{count}")
async def generate_sample_data_api(count: int, subject: Optional[str] = "math"):
    """生成示例数据用于演示"""
    try:
        samples = analytics_engine.generate_sample_data(count, subject)
        return {"samples": samples, "count": len(samples)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/analytics/progress/{student_id}")
async def get_student_progress_api(student_id: str):
    """获取学生学习进度追踪数据"""
    try:
        progress = analytics_engine.get_progress_tracking(student_id)
        return progress
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/analytics/comparison")
async def get_metrics_comparison_api():
    """获取与传统批改方法的对比数据"""
    try:
        comparison = analytics_engine.calculate_metrics_comparison()
        return comparison
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/analytics/export-report")
async def export_analytics_report_api(format: Optional[str] = "json"):
    """导出分析报告"""
    try:
        report_path = analytics_engine.export_analytics_report(format)
        return {"report_path": report_path, "format": format}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/analytics/current-stats")
async def get_current_stats_api():
    """获取当前批改统计数据"""
    try:
        if not analytics_engine.batch_results:
            return {"message": "暂无批改数据，请先使用批量批改功能"}
        
        analytics = analytics_engine._calculate_batch_analytics(analytics_engine.batch_results)
        return {
            "total_submissions": len(analytics_engine.batch_results),
            "analytics": analytics
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

from fastapi.staticfiles import StaticFiles

# ==================== Rubric 评分标准 API ====================

# Rubric 请求模型
class RubricCriterionLevel(BaseModel):
    score: float
    description: str

class RubricCriterionModel(BaseModel):
    id: Optional[str] = None
    name: str
    weight: float
    description: str = ""
    levels: List[dict]

class RubricCreateRequest(BaseModel):
    name: str
    subject: str
    description: str = ""
    criteria: List[dict]

class RubricUpdateRequest(BaseModel):
    name: str
    subject: str
    description: str = ""
    criteria: List[dict]

class RubricGradeRequest(BaseModel):
    content: str
    student_id: Optional[str] = None

@api_router.get("/rubric/list")
async def list_rubrics_api(subject: Optional[str] = None):
    """获取评分标准列表"""
    rubrics = rubric_engine.list_rubrics(subject)
    return {"rubrics": rubrics, "total": len(rubrics)}

@api_router.get("/rubric/{rubric_id}")
async def get_rubric_api(rubric_id: str):
    """获取单个评分标准详情"""
    rubric = rubric_engine.get_rubric(rubric_id)
    if not rubric:
        raise HTTPException(status_code=404, detail="评分标准不存在")
    return rubric

@api_router.post("/rubric")
async def create_rubric_api(req: RubricCreateRequest):
    """创建评分标准"""
    result = rubric_engine.create_rubric(
        name=req.name, subject=req.subject,
        description=req.description, criteria=req.criteria
    )
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["errors"])
    return result["rubric"]

@api_router.put("/rubric/{rubric_id}")
async def update_rubric_api(rubric_id: str, req: RubricUpdateRequest):
    """更新评分标准"""
    result = rubric_engine.update_rubric(
        rubric_id, name=req.name, subject=req.subject,
        description=req.description, criteria=req.criteria
    )
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["errors"])
    return result["rubric"]

@api_router.delete("/rubric/{rubric_id}")
async def delete_rubric_api(rubric_id: str):
    """删除评分标准"""
    result = rubric_engine.delete_rubric(rubric_id)
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["errors"])
    return {"success": True, "message": "删除成功"}

@api_router.get("/rubric/templates/list")
async def get_templates_api():
    """获取预设模板列表"""
    templates = rubric_engine.get_templates()
    return {"templates": templates, "total": len(templates)}

@api_router.post("/rubric/templates/{template_id}/clone")
async def clone_template_api(template_id: str, new_name: str = "克隆的评分标准"):
    """克隆预设模板"""
    result = rubric_engine.clone_template(template_id, new_name)
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["errors"])
    return result["rubric"]

@api_router.post("/rubric/{rubric_id}/grade")
async def grade_with_rubric_api(rubric_id: str, req: RubricGradeRequest):
    """使用评分标准批改作业"""
    result = rubric_engine.grade_with_rubric(rubric_id, req.content, req.student_id)
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["errors"])
    return result

app.include_router(api_router)
app.mount("/", StaticFiles(directory="../frontend/dist", html=True), name="static")

if __name__ == "__main__":
    # 从环境变量读取端口（适配沙箱环境）
    port = int(os.environ.get("DEPLOY_RUN_PORT", 8000))
    print(f"🚀 EduChat 服务启动在端口 {port}")
    uvicorn.run(app, host="0.0.0.0", port=port)