# 基礎階段：安裝 uv
FROM python:3.12-slim-bookworm AS base
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/
WORKDIR /app

# 定義環境文件參數
ARG ENV_FILE=.env-dev

# 開發階段：包含所有開發工具和依賴
FROM base AS development

ARG ENV_FILE
# 安裝開發工具
RUN apt-get update && apt-get install -y \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 複製依賴文件
COPY pyproject.toml README.md ./

# 安裝所有依賴（包括開發依賴）
RUN uv sync --dev

# 複製環境文件
COPY ${ENV_FILE} ./.env

# 複製源代碼
COPY . .

# 設置開發環境變數
ENV PYTHONPATH=/app/src
ENV PYTHONUNBUFFERED=1
ENV ENVIRONMENT=development

# 默認開發命令
CMD ["uv", "run", "cleansales-api"]

# 生產階段：只包含運行必需的文件
FROM base AS production
# 繼承 ARG
ARG ENV_FILE

# 複製依賴文件
COPY pyproject.toml README.md ./

# 只安裝生產依賴
RUN uv sync

# 複製環境文件
COPY ${ENV_FILE} ./.env

# 複製源代碼
COPY ./src /app/src
COPY ./data /app/data

# 設置生產環境變數
ENV PYTHONPATH=/app/src
ENV PYTHONUNBUFFERED=1
ENV ENVIRONMENT=production

# 生產環境命令
CMD ["uv", "run", "cleansales-api"]