# 1. base 階段：定義基礎映像檔和 UV 變數
FROM ghcr.io/astral-sh/uv:python3.12-alpine AS base
WORKDIR /app

ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy

# 2. dev 階段：開發者環境
FROM base AS development
# 安裝開發工具
RUN apk add --no-cache git curl

# 複製依賴文件
ADD pyproject.toml uv.lock . 
RUN uv sync --frozen --no-install-project

# 複製源代碼
ADD ./src /app/src

RUN uv sync --dev

# 設置開發環境變數
ENV PYTHONPATH=/app/src
ENV PYTHONUNBUFFERED=1


# 3. production 階段：生產環境
FROM base AS production
# 複製依賴文件
COPY pyproject.toml uv.lock . 

# 安裝生產依賴
RUN uv sync

# 複製源代碼
COPY ./src /app/src

# 設置生產環境變數
ENV PYTHONPATH=/app/src
ENV PYTHONUNBUFFERED=1
