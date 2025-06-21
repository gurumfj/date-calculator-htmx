FROM ghcr.io/astral-sh/uv:python3.13-alpine

WORKDIR /app

ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy
ENV PYTHONPATH=/app/src
ENV PYTHONUNBUFFERED=1

# 複製依賴文件並安裝
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-install-project

# 複製源代碼
COPY src /app/src

# 創建必要的目錄
RUN mkdir -p /app/data /app/logs

# 使用 pyproject.toml 中定義的 dev 命令
CMD ["uv", "run", "dev"]
