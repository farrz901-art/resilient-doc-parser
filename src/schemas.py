# from pydantic import BaseModel, Field, field_validator
# import re
# from datetime import datetime
# from typing import List, Optional
#
#
# # --- 基础数据模型 (Inner Data) ---
#
# class LineItem(BaseModel):
#     description: str = Field(..., description="商品或服务的描述")
#     quantity: int = Field(..., description="数量")
#     price: float = Field(..., description="单价")
#     amount: float = Field(..., description="该行的总金额")
#
#
# class Invoice(BaseModel):
#     invoice_number: str = Field(..., description="发票号码")
#     # 日期字段带自愈逻辑
#     date: str = Field(..., description="发票日期，格式为 YYYY-MM-DD")
#
#     # 供应商名字带自愈逻辑（必须含“有限公司”）
#     vendor_name: str = Field(..., description="供应商名称")
#
#     items: List[LineItem] = Field(..., description="发票中的商品列表")
#
#     # 金额字段带自愈逻辑（必须大于10）
#     total_amount: float = Field(..., description="发票总金额")
#     currency: str = Field(default="CNY", description="货币单位")
#
#     # --- 自愈逻辑 Validator ---
#
#     @field_validator('date')
#     @classmethod
#     def normalize_date(cls, v: str) -> str:
#         # 清洗干扰字符，比如 "(缺少年份)" 这种括号里的内容
#         v = re.sub(r'\(.*?\)', '', v).strip()  # 去掉括号及内容
#
#         # 简单处理中文
#         v = v.replace('年', '-').replace('月', '-').replace('日', '')
#
#         # 如果模型只输出了 "2/15" 或 "2-15"，我们代码里帮它补全 2024
#         # 这叫 "Rule-based Fallback" (规则兜底)
#         if re.match(r'^\d{1,2}[/-]\d{1,2}$', v):
#             v = f"2024-{v.replace('/', '-')}"
#
#         try:
#             dt = datetime.strptime(v, "%Y-%m-%d")
#             return dt.strftime("%Y-%m-%d")
#         except ValueError:
#             # 尝试其他格式...
#             try:
#                 dt = datetime.strptime(v, "%Y/%m/%d")
#                 return dt.strftime("%Y-%m-%d")
#             except ValueError:
#                 raise ValueError(f"日期格式必须是 YYYY-MM-DD，收到的值是: {v}")
#
#     @field_validator('vendor_name')
#     @classmethod
#     def validate_vendor(cls, v: str) -> str:
#         # 自愈逻辑：强制补全公司全称
#         if "有限公司" not in v:
#             # 这里抛出异常，触发重试，让 LLM 去补全
#             raise ValueError(
#                 f"供应商名称 '{v}' 不规范，必须包含 '有限公司' 全称。如果原文没有，请尝试补全或根据上下文推断。")
#         return v
#
#     @field_validator('total_amount')
#     @classmethod
#     def validate_amount(cls, v: float) -> float:
#         if v < 10.0:
#             raise ValueError(f"金额异常：{v}，发票金额不能小于 10.0")
#         return v
#
#
# # --- 顶层结果包装 (Outer Wrapper) ---
#
# class ExtractionResult(BaseModel):
#     """
#     这是最终返回给 API 的对象，包含业务数据和元数据
#     """
#     # 核心业务数据
#     invoice_data: Invoice = Field(..., description="提取出的发票核心数据")
#
#     # 元数据：置信度
#     confidence_score: float = Field(
#         ...,
#         description="0.0到1.0之间的小数，表示对提取结果的自信程度。1.0表示非常自信（字迹清晰、格式完美），0.1表示完全瞎猜（模糊不清）。",
#         ge=0.0,
#         le=1.0
#     )
#
#     # 元数据：备注
#     notes: str = Field(
#         default="",
#         description="模型对提取过程的备注，比如'字迹模糊'、'缺角'或'日期格式不规范已自动修正'等信息。"
#     )