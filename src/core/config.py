# src/core/config.py
import os

# 优先读取环境变量，如果没有则用默认值 (本地开发用)
# host.docker.internal 是 Docker 特有的宿主机域名
DEFAULT_LM_STUDIO_URL = "http://localhost:1234/v1"
LM_STUDIO_API_BASE = os.getenv("LM_STUDIO_API_BASE", DEFAULT_LM_STUDIO_URL)
API_KEY = "lm-studio"

# 模型名称
MODEL_NAME = "gemma-2-9b-it"

# 默认超时时间
TIMEOUT = 600.0