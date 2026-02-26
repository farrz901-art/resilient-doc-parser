# Resilient Doc Parser (自愈式智能文档流水线)



![License](https://img.shields.io/badge/license-MIT-blue)
![Python](https://img.shields.io/badge/python-3.10-green)
![Docker](https://img.shields.io/badge/docker-ready-blue)

> **不仅仅是 OCR。**
> 这是一个基于 **Local LLM (Gemma-2)** + **RapidOCR** + **Human-in-the-loop** 的企业级智能文档处理中台。



## 核心特性 (Features)

-   **语义自愈 (Self-Healing)**: 自动修复 OCR 乱码、日期格式错误，拒绝幻觉。
-   **多模态摄取 (Multi-modal)**: 支持 PDF (文本/扫描件)、Word、Markdown、图片。
-   **智能路由 (Smart Router)**: 自动识别文档类型 (发票 vs 合同) 并分发给不同提取器。
-   **异步高并发**: 基于 **Celery + Redis** 架构，支持海量文件排队处理。
-   **人机协同 (HITL)**: 提供 Streamlit 审核界面，允许人工修正数据并回流训练。
-   **开放生态**: 支持 Webhook 推送，轻松集成到钉钉/飞书/ERP。





![image-20260226191245294](C:\Users\LENOVO\AppData\Roaming\Typora\typora-user-images\image-20260226191245294.png)





## 🏗️ 架构设计 (Architecture)

![deepseek_mermaid_20260226_54cf12](D:\LianxiangDownload\deepseek_mermaid_20260226_54cf12.png)



## 🚀 快速开始 (Quick Start)

### 前置要求

-   Docker Desktop (已启动)
-   LM Studio (加载 Gemma-2-9b-it 模型，开启 Server 模式)

### 一键启动

```
# 1. 克隆仓库
git clone https://github.com/yourname/resilient-doc-parser.git
cd resilient-doc-parser

# 2. 启动服务 (自动构建镜像)
docker-compose up --build -d
```

### 访问服务

-   **前端工作台**: [http://localhost:8501](http://localhost:8501/)
-   **API 文档**: http://localhost:8000/docs
-   **Redis 监控**: (可选) docker exec -it doc-parser-redis redis-cli



## 📂 项目结构

```
src/
├── core/           # 核心组件 (OCR引擎, 数据库, LLM客户端)
├── parsers/        # 业务解析器 (发票, 合同...)
├── worker.py       # Celery 后台任务逻辑
├── router.py       # 智能分类路由
├── main.py         # FastAPI 入口
└── dashboard.py    # Streamlit 前端
```



## 🛠️ 技术栈

-   **后端**: FastAPI, Celery, SQLAlchemy
-   **AI/OCR**: LlamaIndex, RapidOCR (ONNX), Gemma-2 (Local)
-   **前端**: Streamlit
-   **中间件**: Redis, SQLite
-   **部署**: Docker Compose



## 🤝 贡献 (Contributing)

欢迎提交 PR！目前正在寻找以下方向的贡献者：

1.  支持更多文档类型 (简历, 银行流水)。
2.  强化流水线健壮度。
3.  优化 GPU 推理速度。



## 📄 License

MIT © 2026 farrz901-art