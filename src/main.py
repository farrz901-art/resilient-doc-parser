# src/main.py
from fastapi import FastAPI, UploadFile, File, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from src.core.database import init_db, get_db, ExtractionLog
from src.router import route_and_extract
from src.core.ingest import parse_file
import json
from pydantic import BaseModel
from typing import Optional, Any, List
from datetime import datetime
from src.worker import process_document_task # 导入 Celery 任务
import shutil
import os

# 初始化数据库 (自动创建 data.db)
init_db()

app = FastAPI(title="Resilient Doc Parser v2.3 (DB + History API)")


# --- Pydantic Models for Response ---
class ExtractResponse(BaseModel):
    id: int
    status: str
    data: Optional[Any] = None
    doc_type: Optional[str] = None
    error: Optional[str] = None
    confidence_score: float = 0.0
    raw_text_preview: Optional[str] = None


class HistoryItem(BaseModel):
    id: int
    filename: str
    doc_type: Optional[str]
    status: str
    confidence: Optional[float]
    created_at: datetime

    # 列表页不需要返回 huge JSON data
    class Config:
        from_attributes = True


class HistoryDetail(HistoryItem):
    data: Optional[Any] = None
    error_message: Optional[str] = None


# --- API Endpoints ---

# 确保上传目录存在
UPLOAD_DIR = "/app/uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@app.post("/extract", response_model=ExtractResponse)
async def extract_api(
        file: UploadFile = File(...),
        db: Session = Depends(get_db)
):
    """
    上传文件 -> 解析 -> 提取 -> 存库
    """
    """
        异步版提取接口：
        1. 存文件
        2. 建记录 (Pending)
        3. 发任务
        4. 立刻返回
    """
    print(f"📂 收到文件: {file.filename}")

    try:
        # 1. 保存文件到共享卷
        file_path = os.path.join(UPLOAD_DIR, file.filename)
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # 2. 创建数据库记录 (初始状态: pending)
        new_log = ExtractionLog(
            filename=file.filename,
            status="pending",  # 新增状态
            confidence=0.0
        )
        db.add(new_log)
        db.commit()
        db.refresh(new_log)

        # 3. 发送异步任务
        # .delay() 是 Celery 的异步调用方法
        process_document_task.delay(new_log.id, file_path)

        print(f"🚀 任务已入队，ID: {new_log.id}")

        # 4. 立刻返回 (前端会看到状态是 pending)
        return {
            "id": new_log.id,
            "status": "pending",
            "data": None,
            "doc_type": None,
            "error": None,
            "confidence_score": 0.0,
            "raw_text_preview": "Processing in background..."
        }

    except Exception as e:
        return {
            "id": -1,
            "status": "failed",
            "error": str(e),
            "data": None
        }


@app.get("/history", response_model=List[HistoryItem])
def get_history(
        skip: int = 0,
        limit: int = 50,
        db: Session = Depends(get_db)
):
    """
    获取历史记录列表 (分页)
    """
    logs = db.query(ExtractionLog).order_by(ExtractionLog.created_at.desc()).offset(skip).limit(limit).all()
    return logs


@app.get("/history/{log_id}", response_model=HistoryDetail)
def get_log_detail(log_id: int, db: Session = Depends(get_db)):
    """
    获取单条记录详情
    """
    log = db.query(ExtractionLog).filter(ExtractionLog.id == log_id).first()
    if not log:
        raise HTTPException(status_code=404, detail="Log not found")

    # 手动构造返回对象，因为数据库存的是 JSON 字符串
    return HistoryDetail(
        id=log.id,
        filename=log.filename,
        doc_type=log.doc_type,
        status=log.status,
        confidence=log.confidence,
        created_at=log.created_at,
        data=log.get_data(),  # 这里调用 database.py 里的 helper 方法
        error_message=log.error_message
    )


@app.delete("/history/{log_id}")
def delete_log(log_id: int, db: Session = Depends(get_db)):
    """
    删除单条记录
    """
    log = db.query(ExtractionLog).filter(ExtractionLog.id == log_id).first()
    if not log:
        raise HTTPException(status_code=404, detail="Log not found")

    db.delete(log)
    db.commit()
    return {"message": "Deleted successfully"}


@app.delete("/history")
def clear_history(db: Session = Depends(get_db)):
    """
    清空所有历史记录
    """
    db.query(ExtractionLog).delete()
    db.commit()
    return {"message": "All history cleared"}





# 定义更新请求的数据结构
class UpdateLogRequest(BaseModel):
    # 允许用户修改整个 data 对象
    data: Any
    # 允许用户手动标记状态 (比如改为 success)
    status: Optional[str] = "reviewed"


@app.patch("/history/{log_id}")
def update_log(
        log_id: int,
        update_req: UpdateLogRequest,
        db: Session = Depends(get_db)
):
    """
    更新单条记录的数据 (人工修正)
    """
    log = db.query(ExtractionLog).filter(ExtractionLog.id == log_id).first()
    if not log:
        raise HTTPException(status_code=404, detail="Log not found")

    # 更新数据
    # 注意：要将 Pydantic/Dict 转回 JSON 字符串存入 SQLite
    try:
        log.result_json = json.dumps(update_req.data)
        log.status = update_req.status
        # 如果人工修正了，置信度可以视为 1.0 (或者保持原样，这里我们标记为 1.0 表示人工确认)
        log.confidence = 1.0

        db.commit()
        db.refresh(log)
        return {"message": "Updated successfully", "id": log.id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Update failed: {str(e)}")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)