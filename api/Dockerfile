# 使用 ARM64 架构的 Python 3.11 镜像
FROM arm64v8/python:3.11

# 可选：使用清华大学镜像源加速下载（如果网络环境需要）
ENV PIP_INDEX_URL=https://pypi.tuna.tsinghua.edu.cn/simple
ENV PIP_NO_CACHE_DIR=on

# 设置工作目录
WORKDIR /app

# 先复制 requirements.txt 并安装依赖（利用 Docker 缓存层）
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY . /app

# 暴露端口（根据您的项目，使用 8000 端口）
EXPOSE 8000

# 启动命令（根据您的项目结构调整）
CMD ["uvicorn", "main_sse:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]