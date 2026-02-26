# 使用官方轻量级 Python 3.10 镜像
FROM python:3.12-slim

# 设置工作目录
WORKDIR /app

# ⚠️ 关键修改：更换 Debian 软件源为阿里云源 (极大提升下载速度和稳定性)
RUN sed -i 's/deb.debian.org/mirrors.aliyun.com/g' /etc/apt/sources.list.d/debian.sources 2>/dev/null || \
    sed -i 's/deb.debian.org/mirrors.aliyun.com/g' /etc/apt/sources.list

# 再次尝试安装系统依赖
# 增加 --fix-missing 参数以增强容错性
RUN apt-get update && apt-get install -y --no-install-recommends --fix-missing \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# 设置 pip 源为清华源
ENV PIP_INDEX_URL=https://pypi.tuna.tsinghua.edu.cn/simple

# 复制依赖文件
COPY requirements.txt .

# 安装 Python 依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制项目代码
COPY src/ ./src/

# 暴露端口
EXPOSE 8000

# 启动命令
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]