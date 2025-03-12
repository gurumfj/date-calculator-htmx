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

from .routers import query, upload

# 配置日誌記錄器
logger = logging.getLogger(__name__)

# FastAPI 應用程式配置
# -----------------------------------------------------------------------------
app = FastAPI(
    title="銷售資料處理 API",
    description="""
    提供銷售資料處理服務的 API
    
    ## 功能
    - 上傳 Excel 檔案進行處理
    - 支援 .xlsx 和 .xls 格式
    - 返回處理結果和錯誤訊息
    
    ## 使用方式
    1. 使用 POST `/upload/sales` 上傳販售資料 Excel 檔案
    2. 使用 POST `/upload/breeds` 上傳入雛資料 Excel 檔案
    3. 系統會自動處理檔案並返回結果
    
    ## 注意事項
    - 檔案大小限制：10MB
    - 支援的 Excel 版本：2007 及以上
    - 處理時間依檔案大小而定
    """,
    version="1.0.0",
)

# 註冊 API 路由
app.include_router(query.router)  # 這會處理 /api/not-completed
app.include_router(upload.router)  # 這會處理 /api/upload


# 健康檢查端點
@app.get("/")
async def health_check():
    """
    健康檢查端點
    返回服務狀態和版本信息
    """
    return {"status": "healthy", "service": "CleanSales API", "version": "1.0.0"}


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
