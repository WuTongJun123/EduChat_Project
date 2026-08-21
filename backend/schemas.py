from pydantic import BaseModel
from typing import Optional

class GradeRequest(BaseModel):
    content: str
    max_tokens: Optional[int] = 1024
    subject: Optional[str] = None   # 可选，如"数学"、"语文"等
    temperature: Optional[float] = None   # 可选，0.1~1.0，控制输出随机性
    prompt_type: Optional[str] = None     # 可选，"basic"/"structured"/"cot"
    detail_level: Optional[str] = None    # 可选，"brief"/"normal"/"detailed"/"deep"

class GradeResponse(BaseModel):
    result: str