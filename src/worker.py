# src/worker.py
import os
import json
from celery import Celery
from sqlalchemy.orm import Session
from src.core.database import SessionLocal, ExtractionLog
from src.core.ingest import parse_file
from src.router import route_and_extract
import io
import requests


# Webhook 地址 (可以是钉钉机器人、飞书、或者你的下游业务系统)
# 这里为了测试，可以用 webhook.site 生成一个临时的
WEBHOOK_URL = os.getenv("WEBHOOK_URL", "")

# 获取 Redis 地址
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

# 初始化 Celery 应用
celery_app = Celery(
    "doc_parser",
    broker=REDIS_URL,
    backend=REDIS_URL
)


# ⚠️ 关键：模拟 FastAPI UploadFile 的行为
# 这样我们就不用改写 ingest.py 的逻辑了
class LocalFileWrapper:
    def __init__(self, path: str, filename: str):
        self.path = path
        self.filename = filename
        self.file = open(path, "rb")  # 以二进制模式打开本地文件

    def close(self):
        self.file.close()


@celery_app.task(bind=True)
def process_document_task(self, log_id: int, file_path: str):
    """
    Celery 后台任务：
    1. 读本地文件 -> 伪装成 UploadFile -> 调用 ingest -> OCR
    2. LLM 提取
    3. 更新数据库
    """
    print(f"🚀 [Worker] 开始处理任务 ID: {log_id}, 文件: {file_path}")

    db: Session = SessionLocal()
    # 获取日志对象
    log = db.query(ExtractionLog).filter(ExtractionLog.id == log_id).first()

    if not log:
        print(f"❌ [Worker] 日志 ID {log_id} 不存在")
        return "Log not found"

    try:
        # 1. 标记为处理中
        log.status = "processing"
        db.commit()

        # 2. 构造假对象并调用 OCR
        filename = os.path.basename(file_path)

        # 使用上下文管理器确保文件关闭
        file_wrapper = LocalFileWrapper(file_path, filename)
        try:
            # 这一步是最耗时的，现在它在后台运行了！
            text_content = parse_file(file_wrapper)
        finally:
            file_wrapper.close()

        if text_content.startswith("ERROR:"):
            raise Exception(text_content)

        print(f"📄 [Worker] OCR 完成，文本长度: {len(text_content)}")

        # 3. LLM 智能提取
        result = route_and_extract(text_content)

        # 4. 更新数据库
        status = "success"
        if result.confidence_score < 0.8:
            status = "review_needed"
        if result.doc_type == "unknown" or result.doc_type == "error":
            status = "failed"

        log.doc_type = result.doc_type
        log.status = status
        log.confidence = result.confidence_score

        # 序列化 JSON
        json_data = result.data.model_dump() if result.data and hasattr(result.data, 'model_dump') else result.data
        log.result_json = json.dumps(json_data)
        log.error_message = result.notes if status == "failed" else None

        db.commit()
        print(f"✅ [Worker] 任务完成！状态: {status}")

        # # ---------------------------------------------
        # # 5. Webhook 推送 (新增逻辑)
        # # ---------------------------------------------
        # if WEBHOOK_URL and status == "success":
        #     try:
        #         payload = {
        #             "event": "extraction_completed",
        #             "task_id": log_id,
        #             "filename": log.filename,
        #             "doc_type": log.doc_type,
        #             "data": json_data  # 提取出的结果
        #         }
        #         requests.post(WEBHOOK_URL, json=payload, timeout=5)
        #         print(f"🔔 Webhook 推送成功: {WEBHOOK_URL}")
        #     except Exception as e:
        #         print(f"⚠️ Webhook 推送失败: {e}")

        return "Success"

    except Exception as e:
        print(f"❌ [Worker] 任务失败: {e}")
        log.status = "failed"
        log.error_message = str(e)
        db.commit()
        return f"Failed: {e}"

    finally:
        db.close()
        # 可选：处理完删除临时文件，释放空间
        # if os.path.exists(file_path):
        #     os.remove(file_path)