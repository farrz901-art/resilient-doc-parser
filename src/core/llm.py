# src/core/llm.py
import httpx
from llama_index.llms.openai_like import OpenAILike
from src.core.config import LM_STUDIO_API_BASE, API_KEY, MODEL_NAME, TIMEOUT


def get_llm(temperature: float = 0.1):
    """
    获取 LlamaIndex LLM 实例
    """
    # trust_env=False 防止本地代理干扰
    http_client = httpx.Client(timeout=TIMEOUT, trust_env=False)

    llm = OpenAILike(
        model=MODEL_NAME,
        api_base=LM_STUDIO_API_BASE,
        api_key=API_KEY,
        is_chat_model=True,
        timeout=TIMEOUT,
        http_client=http_client,
        temperature=temperature
    )
    return llm