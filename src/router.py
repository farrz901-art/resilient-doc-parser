# src/router.py
from pydantic import BaseModel, Field
from llama_index.core.program import LLMTextCompletionProgram
from src.core.llm import get_llm
from src.core.models import BaseExtractionResult
# 引入具体的解析器
from src.parsers import invoice, contract


# 定义分类器的输出结构
class ClassifyResult(BaseModel):
    doc_type: str = Field(..., description="只能是 'invoice', 'contract' 或 'unknown'")


def route_and_extract(text: str) -> BaseExtractionResult:
    print("🚦 正在进行文档分类...")

    # --- 1. 智能分类阶段 ---

    # 截断：分类只需要看前 1000 个字，防止长合同浪费 Token
    classification_snippet = text[:1000]

    llm = get_llm(temperature=0.1)

    # 简单的分类 Prompt
    prompt = (
        "阅读以下文本前段，判断是 'invoice' (发票/收据/小票) 还是 'contract' (合同/协议/标书)？\n"
        "如果无法确定，返回 'unknown'。\n"
        "----------------\n"
        "{text_input}\n"
        "----------------\n"
    )

    program = LLMTextCompletionProgram.from_defaults(
        output_cls=ClassifyResult,
        llm=llm,
        prompt_template_str=prompt
    )

    try:
        # 调用 LLM 进行分类
        cls_res = program(text_input=classification_snippet)
        doc_type = cls_res.doc_type.lower()
    except Exception as e:
        print(f"⚠️ LLM 分类失败，尝试使用关键词兜底: {e}")
        # --- 关键词规则兜底 (Rule-based Fallback) ---
        if "合同" in classification_snippet or "协议" in classification_snippet or "甲方" in classification_snippet:
            doc_type = "contract"
        elif "发票" in classification_snippet or "收款" in classification_snippet or "开票" in classification_snippet:
            doc_type = "invoice"
        else:
            doc_type = "unknown"

    print(f"👉 分类结果: {doc_type}")

    # --- 2. 路由分发阶段 ---

    try:
        if "invoice" in doc_type:
            # 调用发票解析器
            return invoice.parse(text)

        elif "contract" in doc_type:
            # 调用合同解析器
            return contract.parse(text)

        else:
            # 未知类型
            return BaseExtractionResult(
                doc_type="unknown",
                confidence_score=0.0,
                data=None,
                notes="AI 无法识别该文档类型，目前仅支持发票和合同。"
            )

    except Exception as e:
        # --- 3. 全局异常捕获 ---
        # 这一步是为了防止 parser 内部报错导致整个 API 500 崩溃
        # 现在 "error" 是合法的 DocType 了
        error_msg = str(e)
        print(f"💥 路由分发阶段发生严重错误: {error_msg}")

        return BaseExtractionResult(
            doc_type="error",
            confidence_score=0.0,
            data=None,
            notes=f"提取过程崩溃: {error_msg}"
        )