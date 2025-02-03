# 使用 Python 3.12 作為基礎映像
FROM python:3.12-slim

# 設置工作目錄
WORKDIR /app

# 安裝 uv 包管理器
RUN pip install uv

# 複製專案文件
COPY pyproject.toml README.md ./
COPY src/ src/

# 使用 uv 安裝依賴
RUN uv pip install --system -e .

# 暴露端口
EXPOSE 8000

# 設置環境變數
ENV PYTHONPATH=/app/src
ENV PYTHONUNBUFFERED=1

# 運行應用
CMD ["python", "src/api.py"] 