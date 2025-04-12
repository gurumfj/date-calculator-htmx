# ---- Frontend Stage ----
FROM oven/bun:1 AS deps

WORKDIR /app/frontend

# 只複製 package.json 和 lockfile
COPY frontend/package.json frontend/bun.lock ./

# 安裝依賴
RUN bun install --no-optional && \
    bun add -d @rollup/rollup-linux-arm64-gnu

# 構建階段
FROM oven/bun:1 AS frontend_builder

WORKDIR /app/frontend

# 從依賴項階段複製 node_modules
COPY --from=deps /app/frontend/node_modules ./node_modules

# 複製前端源代碼
COPY frontend/ ./

# 設置生產環境變量
# ENV NODE_ENV=production
# ENV VITE_API_URL=/api

# 構建 frontend dist
RUN bun run build

## ---- Backend Stage ----
# 1. Base 階段：最小化的 Python 環境，僅安裝 production 依賴
FROM ghcr.io/astral-sh/uv:python3.12-alpine AS base
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

# 創建前端靜態文件目錄
RUN mkdir -p /app/frontend/dist

# 複製 frontend dist 的內容到 frontend/dist 目錄
COPY --from=frontend_builder /app/frontend/dist/ /app/frontend/dist/

# 設置 CMD
# CMD ["python", "-m", "src.cleansales_backend.main"]
