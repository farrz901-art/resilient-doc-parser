# src/core/database.py
from sqlalchemy import create_engine, Column, Integer, String, Float, Text, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker
from datetime import datetime
import json

# SQLite 数据库文件路径 (会自动在项目根目录生成 data.db)
DATABASE_URL = "sqlite:///./data.db"

# 创建引擎
# check_same_thread=False 是 SQLite 必须的配置，因为它只允许单线程访问
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

# 创建会话工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 创建基类
Base = declarative_base()


# --- 定义数据表模型 ---
class ExtractionLog(Base):
    __tablename__ = "extraction_logs"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, index=True)
    doc_type = Column(String)  # invoice / contract / unknown
    status = Column(String)  # success / review_needed / failed
    confidence = Column(Float, default=0.0)

    # 存储 JSON 字符串 (SQLite 没有原生 JSON 类型，用 Text 存)
    result_json = Column(Text, nullable=True)

    # 存储错误信息
    error_message = Column(Text, nullable=True)

    # 创建时间
    created_at = Column(DateTime, default=datetime.now)

    # --- 辅助方法 ---
    def get_data(self):
        """
        将 result_json 字符串转回 Python 字典/列表
        """
        if not self.result_json:
            return None
        try:
            return json.loads(self.result_json)
        except json.JSONDecodeError:
            return {"error": "Invalid JSON in database"}


# --- 初始化数据库 (建表) ---
def init_db():
    # 这行代码会自动检测表是否存在，不存在则创建
    Base.metadata.create_all(bind=engine)


# --- 依赖注入 (FastAPI 用) ---
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()