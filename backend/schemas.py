from pydantic import BaseModel
from typing import Optional

class GradeRequest(BaseModel):
    content: str
    max_tokens: Optional[int] = 1024
    subject: Optional[str] = None   # 可选，如"数学"、"语文"等

class GradeResponse(BaseModel):
    result: str