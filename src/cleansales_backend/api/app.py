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

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.params import Depends
from fastapi.responses import JSONResponse
from typing_extensions import Annotated

from cleansales_backend.core import settings
from cleansales_backend.services.query_service import QueryService

from .routers import query, upload
from .routers.query import get_query_service

# 配置日誌記錄器
logger = logging.getLogger(__name__)


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
    version="1.0.1",
)

# 註冊 API 路由
app.include_router(query.router)  # 這會處理 /api/not-completed
app.include_router(upload.router)  # 這會處理 /api/upload


# 健康檢查端點
@app.get("/")
async def health_check() -> JSONResponse:
    """
    健康檢查端點
    返回服務狀態和版本信息
    """
    cache_state = get_query_service().get_batch_cache_info()
    return JSONResponse(
        {
            "status": "healthy",
            "branch": settings.BRANCH,
            "cache_state": cache_state,
            "api_version": app.version,
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


# CORS 中間件配置
# -----------------------------------------------------------------------------
# 允許跨域請求，方便前端開發和整合
# TODO: 在生產環境中應該限制 allow_origins 為特定域名
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 開發環境允許所有來源
    allow_credentials=True,  # 允許攜帶認證信息
    allow_methods=["*"],  # 允許所有 HTTP 方法
    allow_headers=["*"],  # 允許所有 HTTP 頭部
)
