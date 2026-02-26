# import os
# import httpx
# from llama_index.llms.openai_like import OpenAILike
# from llama_index.core import Settings
# from llama_index.core.program import LLMTextCompletionProgram
# from src.schemas import ExtractionResult
# from pydantic import ValidationError
#
# # --- 复用你之前的配置逻辑 ---
# LM_STUDIO_API_BASE = "http://192.168.3.15:1234/v1"
# MODEL_NAME = "gemma-2-9b-it"  # 或者你的模型名
#
#
# def get_llm():
#     # 记得加上 trust_env=False 防止 502
#     http_client = httpx.Client(timeout=180.0, trust_env=False)
#     llm = OpenAILike(
#         model=MODEL_NAME,
#         api_base=LM_STUDIO_API_BASE,
#         api_key="lm-studio",
#         is_chat_model=True,
#         timeout=180.0,
#         http_client=http_client,
#         # Gemma 对 JSON 友好，temperature 低一点
#         temperature=0.1
#     )
#     return llm
#
#
# def extract_invoice(text: str) -> ExtractionResult:
#     """
#     核心功能：输入纯文本，输出 Invoice 对象(一次变多次)->核心功能：输入纯文本，输出 ExtractionResult 对象 (包含 Invoice + 置信度)
#     包含【自愈机制】：如果校验失败，会自动把错误信息喂回给 LLM 重试
#     """
#     llm = get_llm()
#
#     # # 定义基础 Prompt 模板
#     # base_prompt_str = (
#     #     "你是一个专业的发票数据提取助手。\n"
#     #     "请从以下文本中提取发票信息，并严格按照 JSON 格式输出。\n"
#     #     "如果有字段缺失，请留空或填 0。\n"
#     #     "---------------------\n"
#     #     "{text_input}\n"
#     #     "---------------------\n"
#     # )
#
#     # 定义 Prompt 模板
#     # 我们强调它不仅要提取数据，还要进行自我评估
#     base_prompt_str = (
#         "你是一个专业的发票数据提取审计员。\n"
#         "任务 1: 从以下文本中提取发票信息。\n"
#         "任务 2: 评估提取的准确性 (confidence_score)。\n"
#         "   - 如果字迹清晰、关键字段(金额、日期、供应商)都找到了，给 0.9-1.0。\n"
#         "   - 如果有猜测成分或字段缺失，给 0.5-0.8。\n"
#         "   - 如果完全看不懂，给 0.0-0.4。\n"
#         "---------------------\n"
#         "{text_input}\n"
#         "---------------------\n"
#     )
#
#     # 初始化 Program，注意 output_cls 变了
#     program = LLMTextCompletionProgram.from_defaults(
#         output_cls=ExtractionResult,  # <--- 关键修改
#         llm=llm,
#         prompt_template_str=base_prompt_str,
#         verbose=True
#     )
#
#     # --- 自愈循环逻辑 ---
#     max_retries = 3
#     last_error_msg = ""
#     current_input_text = text
#
#     for attempt in range(max_retries):
#         try:
#             print(f"🔄 [Attempt {attempt + 1}/{max_retries}] 开始提取...")
#
#             if attempt > 0:
#                 # --- 修改点：增强重试的 Prompt 指令 ---
#                 current_input_text = (
#                     f"{text}\n\n"
#                     f"⚠️ PREVIOUS ATTEMPT FAILED. \n"
#                     f"Error Message: {last_error_msg}\n"
#                     f"----------------\n"
#                     f"CRITICAL INSTRUCTIONS FOR FIXING:\n"
#                     f"1. Date Error: If the year is missing, assume it is '2024'. Format MUST be YYYY-MM-DD.\n"
#                     f"2. Vendor Error: If '有限公司' is missing, please append it to make it a valid company name.\n"
#                     f"3. Amount Error: If the amount is ambiguous, pick the most likely numeric value.\n"
#                     f"4. Output valid JSON only."
#                 )
#                 print(f"   -> 注入错误反馈: {last_error_msg}")
#
#             output = program(text_input=current_input_text)
#
#             # 打印一下模型给自己的打分，方便调试
#             print(f"✅ [Attempt {attempt + 1}] 成功！模型置信度: {output.confidence_score}")
#             return output
#
#         except ValidationError as e:
#             print(f"❌ [Attempt {attempt + 1}] 校验失败！")
#             last_error_msg = str(e)
#
#         except Exception as e:
#             print(f"💥 [Critical Error] {e}")
#             raise e
#
#     error_msg = f"Failed after {max_retries} attempts. Last error: {last_error_msg}"
#     print(error_msg)
#     raise Exception(error_msg)