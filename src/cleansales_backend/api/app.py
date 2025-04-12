"""
################################################################################
# FastAPI 應用程式入口點
#
# 這個模組是整個 API 服務的入口點，負責：
# 1. 配置 FastAPI 應用程式
# 2. 設置中間件
# 3. 註冊路由
#
# 主要功能：
# - 應用程式配置
# - 中間件配置（CORS、日誌等）
# - 路由註冊
# - 健康檢查
################################################################################
"""

import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.params import Depends
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from typing_extensions import Annotated

from cleansales_backend.core.database import get_core_db
from cleansales_backend.services.query_service import QueryService

from . import get_client, settings
from .routers import proxy, query, upload
from .routers.query import get_query_service

# 配置日誌記錄器
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    client = get_client()
    yield
    await client.aclose()


# FastAPI 應用程式配置
# -----------------------------------------------------------------------------
app = FastAPI(
    title="銷售資料處理 API",
    description=f"""
    提供銷售資料處理服務的 API

    ## 功能
    - 上傳 Excel 檔案進行處理
    - 支援 .xlsx 和 .xls 格式
    - 返回處理結果和錯誤訊息

    ## 使用方式
    1. 使用 POST `/upload/sales` 上傳販售資料 Excel 檔案
    2. 使用 POST `/upload/breeds` 上傳入雛資料 Excel 檔案
    3. 系統會自動處理檔案並返回結果

    ## 分支信息
    - 分支: {settings.BRANCH}
    """,
    version="1.1.0",
    lifespan=lifespan,
)


# 註冊 API 路由
app.include_router(query.router)  # 這會處理 /api/not-completed
app.include_router(upload.router)  # 這會處理 /api/upload
app.include_router(proxy.router)  # 這會處理 /api/proxy/* 相關端點

# 根據功能開關載入原始數據 API 路由
if settings.FEATURES_RAW_DATA_API:
    from .routers import raw_data

    app.include_router(raw_data.router)  # 這會處理 /api/raw/* 相關端點
    logger.info("已啟用原始數據API")


# 健康檢查端點
@app.get("/api/health")
async def health_check() -> JSONResponse:
    """
    健康檢查端點
    返回服務狀態和版本信息
    """
    cache_state = get_query_service().get_batch_cache_info()

    config = settings.to_dict_safety()

    return JSONResponse(
        {
            "status": "healthy",
            "api_version": app.version,
            "config": config,
            "db_health": get_core_db().db_health_check(),
            "cache_state": cache_state,
            "proxy_health": await proxy.proxy_health_check(),
        }
    )


@app.get("/cache_clear")
async def cache_clear(
    query_service: Annotated[QueryService, Depends(get_query_service)],
) -> JSONResponse:
    """
    清除所有緩存
    """
    query_service.cache_clear()
    return JSONResponse({"status": "success"})


# 靜態資源處理：先註冊所有API路由後再處理靜態資源
# 將 Vite 的 dist 當作靜態目錄掛載（不處理index.html，我們會在fallback中特別處理）
app.mount("/assets", StaticFiles(directory="frontend/dist/assets"), name="assets")


# 根路徑處理與SPA的fallback：所有未匹配的路由指向index.html
@app.get("/{full_path:path}", response_model=None)
async def serve_frontend(full_path: str) -> FileResponse | JSONResponse:
    """
    處理所有未被API路由捕獲的請求，將其導向前端應用index.html。
    這樣實現了單頁應用（SPA）的路由支持。

    注意：API路由優先級高於此處理器，因為它們已在前面註冊。
    """
    logger.info(f"Request path: {full_path}")
    # 指向前端構建目錄中的index.html
    index_path = Path("frontend/dist/index.html")

    # 如果請求根路徑，或index.html存在且路徑非api，則返回index.html
    if full_path == "" or (index_path.exists() and not full_path.startswith("api")):
        return FileResponse(index_path)

    # 如果未找到或是未處理的API路徑，返回404
    return JSONResponse({"error": "Not Found", "path": full_path}, status_code=404)


# CORS 中間件配置
# -----------------------------------------------------------------------------
# 允許跨域請求，方便前端開發和整合
# TODO: 在生產環境中應該限制 allow_origins 為特定域名
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,  # 開發環境允許所有來源
    allow_credentials=True,  # 允許攜帶認證信息
    allow_methods=["*"],  # 允許所有 HTTP 方法
    allow_headers=["*"],  # 允許所有 HTTP 頭部
    expose_headers=["ETag", "If-None-Match"],
)
