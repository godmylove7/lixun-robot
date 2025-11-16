FROM python:3.10-slim

WORKDIR /app

# 复制依赖文件
COPY pyproject.toml uv.lock ./

# 设置pip清华源
RUN pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple

# 安装 uv 和依赖
RUN pip install uv && \
    uv sync --frozen --no-dev

# 复制应用代码
COPY . .

# 创建数据目录
RUN mkdir -p data/documents data/vector_store logs

# 设置环境变量
ENV PYTHONPATH=/app

# 启动命令
CMD ["uv", "run", "python", "run.py"]