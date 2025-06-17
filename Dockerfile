## ---- Backend Stage ----
# 1. Base 階段：最小化的 Python 環境，僅安裝 production 依賴
FROM ghcr.io/astral-sh/uv:python3.13-alpine AS base
WORKDIR /app


ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy
ENV PYTHONPATH=/app/src
ENV PYTHONUNBUFFERED=1

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-install-project

# 2. Production 階段：基於 base，複製最終的應用代碼
FROM base AS production

# 複製 backend 源代碼
COPY src /app/src

# 複製靜態資源或配置文件
COPY migrations /app/migrations
COPY alembic.ini /app/alembic.ini

# 創建必要的目錄
RUN mkdir -p /app/data

# 設置 CMD
# CMD ["uv", "run", "dev"]
