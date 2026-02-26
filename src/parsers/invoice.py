# src/parsers/invoice.py
from pydantic import BaseModel, Field, field_validator, ValidationError
from typing import List
from llama_index.core.program import LLMTextCompletionProgram
from src.core.llm import get_llm
from src.core.models import BaseExtractionResult
import re
from datetime import datetime


# --- 1. Schema 定义 ---
class LineItem(BaseModel):
    description: str = Field(..., description="商品描述")
    quantity: int = Field(..., description="数量")
    price: float = Field(..., description="单价")
    amount: float = Field(..., description="行总价")


class Invoice(BaseModel):
    invoice_number: str = Field(..., description="发票号")
    vendor_name: str = Field(..., description="供应商名称")
    date: str = Field(..., description="日期 YYYY-MM-DD")
    total_amount: float = Field(..., description="总金额")
    items: List[LineItem] = Field(..., description="明细")

    # --- Validators (自愈逻辑) ---
    @field_validator('vendor_name')
    @classmethod
    def validate_vendor(cls, v: str) -> str:
        if "有限公司" not in v:
            raise ValueError(f"供应商 '{v}' 不完整，需包含'有限公司'")
        return v

    @field_validator('date')
    @classmethod
    def normalize_date(cls, v: str) -> str:
        # 简单清洗
        v = v.replace('/', '-').replace('年', '-').replace('月', '-').replace('日', '')
        if re.match(r'^\d{1,2}-\d{1,2}$', v):
            v = f"2024-{v}"
        return v


# --- 2. 内部包装类 ---
class InvoiceWrapper(BaseModel):
    invoice: Invoice
    confidence: float
    notes: str


# --- 3. 提取逻辑 (含重试) ---
def parse(text: str) -> BaseExtractionResult:
    llm = get_llm(temperature=0.1)

    prompt_tmpl = (
        "你是发票提取专家。请提取数据并自查置信度。\n"
        "{text_input}\n"
    )

    program = LLMTextCompletionProgram.from_defaults(
        output_cls=InvoiceWrapper,
        llm=llm,
        prompt_template_str=prompt_tmpl,
        verbose=True
    )

    # 自愈重试循环
    max_retries = 3
    current_text = text
    last_error = ""

    for i in range(max_retries):
        try:
            if i > 0:
                print(f"🔄 Invoice Retry {i + 1}: 注入错误信息 -> {last_error}")
                current_text = f"{text}\n\n⚠️ PREVIOUS ERROR: {last_error}\nFix it."

            output = program(text_input=current_text)

            return BaseExtractionResult(
                doc_type="invoice",
                confidence_score=output.confidence,
                data=output.invoice,  # 这里 data 是 Invoice 对象
                notes=output.notes
            )
        except Exception as e:
            last_error = str(e).split('[type=')[0][:300]
            print(f"❌ Invoice Attempt {i + 1} Failed: {last_error}")

    raise Exception(f"Invoice extraction failed: {last_error}")