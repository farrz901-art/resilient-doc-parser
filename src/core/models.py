# src/core/models.py
from pydantic import BaseModel, Field
from typing import Any, Literal, Optional

# 定义支持的文档类型
DocType = Literal["invoice", "contract", "unknown", "error"]

class BaseExtractionResult(BaseModel):
    """
    所有解析器最终返回的统一格式
    """
    doc_type: DocType = Field(..., description="文档类型")
    confidence_score: float = Field(..., description="置信度 0.0 - 1.0")
    # data 使用 Any，因为不同文档的结构完全不同
    # data: Any = Field(..., description="结构化数据")
    # data 使用 Any，因为不同文档的结构完全不同，允许为 None
    data: Optional[Any] = Field(None, description="结构化数据")
    notes: str = Field(default="", description="备注信息")