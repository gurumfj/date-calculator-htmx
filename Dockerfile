# 1. Base 階段：最小化的 Python 環境，僅安裝 production 依賴
FROM ghcr.io/astral-sh/uv:python3.12-alpine AS base
WORKDIR /app

ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy
ENV PYTHONPATH=/app/src
ENV PYTHONUNBUFFERED=1

COPY pyproject.toml uv.lock ./ 
RUN uv sync --frozen --no-install-project

# 2. Development 階段：基於 base，安裝開發工具和 dev 依賴，並複製源代碼
FROM base AS development
RUN uv sync --dev

# 3. Production 階段：基於 base，複製最終的應用代碼
FROM base AS production
COPY ./src /app/src