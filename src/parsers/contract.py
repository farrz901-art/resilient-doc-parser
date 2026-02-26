# src/parsers/contract.py
import json
import re
from pydantic import BaseModel, Field
from typing import Optional, Any
from llama_index.core.llms import ChatMessage
from src.core.llm import get_llm
from src.core.models import BaseExtractionResult


# --- 1. Schema 定义 ---
class Contract(BaseModel):
    title: Optional[str] = Field(None, description="合同标题")
    party_a: Optional[str] = Field(None, description="甲方名称")
    party_b: Optional[str] = Field(None, description="乙方名称")
    total_value: Optional[float] = Field(None, description="合同总额")
    risk_clauses: Optional[str] = Field(None, description="风险条款摘要")


# --- 2. 辅助函数 ---
def clean_json_string(text: str) -> str:
    text = re.sub(r'^```json\s*', '', text, flags=re.MULTILINE | re.IGNORECASE)
    text = re.sub(r'^```\s*', '', text, flags=re.MULTILINE)
    text = re.sub(r'```\s*$', '', text, flags=re.MULTILINE)
    return text.strip()


# --- 3. 核心逻辑 ---
def parse(text: str) -> BaseExtractionResult:
    # 给合同提取多一点耐心，或者可以在这里单独设置 timeout
    llm = get_llm(temperature=0.1)

    # truncated_text = text[:15000]
    # ⚠️ 关键修改：智能截断策略 (Smart Truncation)
    # 4096 context window 约为 3000 中文字。
    # 我们保留前 2000 字 (含甲乙方、金额) + 后 1000 字 (含签字盖章)
    if len(text) > 3000:
        print(f"✂️ 文本过长 ({len(text)} 字)，执行智能截断...")
        truncated_text = text[:2000] + "\n\n...[中间条款省略]...\n\n" + text[-1000:]
    else:
        truncated_text = text

    # ⚠️ 关键修改：给出明确的 JSON 示例，防止模型过度发挥
    system_prompt = (
        "你是一个资深法务助手。请提取合同关键信息。\n"
        "Strictly output only the following JSON fields. Do not add nested objects or extra fields.\n"
        "Required JSON Structure Example:\n"
        "{\n"
        '  "contract": {\n'
        '      "title": "技术服务合同",\n'
        '      "party_a": "甲方公司名",\n'
        '      "party_b": "乙方公司名",\n'
        '      "total_value": 10000.00,\n'
        '      "risk_clauses": "违约责任...赔偿..."\n'
        "  },\n"
        '  "confidence": 0.9,\n'
        '  "notes": ""\n'
        "}\n"
        "如果找不到金额，total_value 填 null。risk_clauses 请用一段话总结，不要列出所有条款。"
    )

    user_prompt = f"合同文本如下:\n---------------------\n{truncated_text}\n---------------------\n请提取并输出 JSON。"

    try:
        print("⏳ 正在调用 LLM 提取合同 (这可能需要几分钟)...")
        response = llm.chat(messages=[
            ChatMessage(role="system", content=system_prompt),
            ChatMessage(role="user", content=user_prompt)
        ])

        raw_content = response.message.content
        # print(f"🤖 原始输出: {raw_content[:200]}...") # 调试用

        json_str = clean_json_string(raw_content)
        parsed_json = json.loads(json_str)

        # 兼容性处理
        if "contract" in parsed_json:
            contract_data = parsed_json["contract"]
            confidence = parsed_json.get("confidence", 0.8)
            notes = parsed_json.get("notes", "")
        else:
            contract_data = parsed_json
            confidence = 0.5
            notes = "Structure mismatch, mapped directly."

        contract_obj = Contract(**contract_data)

        return BaseExtractionResult(
            doc_type="contract",
            confidence_score=float(confidence),
            data=contract_obj,
            notes=notes
        )

    except json.JSONDecodeError as e:
        print(f"❌ JSON 解析失败: {e}")
        return BaseExtractionResult(
            doc_type="contract",
            confidence_score=0.0,
            data=None,
            notes=f"JSON 格式错误: {str(e)}"
        )

    except Exception as e:
        print(f"❌ 处理异常: {e}")
        return BaseExtractionResult(
            doc_type="contract",
            confidence_score=0.0,
            data=None,
            notes=f"系统错误: {str(e)}"
        )