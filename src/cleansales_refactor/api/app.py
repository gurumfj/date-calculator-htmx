"""
################################################################################
# CleanSales API 主應用程式
#
# 這個模組實現了 CleanSales 的主要 FastAPI 應用程式。它負責：
# 1. API 服務器的配置和初始化
# 2. 日誌系統的設置
# 3. 中間件的配置（CORS、靜態文件）
# 4. 路由的註冊和管理
################################################################################
"""

import logging
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .routers import query, upload

# 配置日誌系統
# -----------------------------------------------------------------------------
# 設定根 logger，使用 DEBUG 級別以捕獲所有重要信息
# 格式包含：時間戳、logger名稱、日誌級別和具體消息
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)

# 配置特定的處理器 logger
# 這個 logger 專門用於處理銷售數據的核心邏輯
processor_logger = logging.getLogger("cleansales_refactor.processor")
processor_logger.setLevel(logging.DEBUG)
# 確保所有 handler 都使用相同的日誌級別
for handler in processor_logger.handlers:
    handler.setLevel(logging.DEBUG)

# API 專用的 logger 實例
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

# 靜態文件服務配置
# -----------------------------------------------------------------------------
# 設定靜態文件目錄，用於服務前端資源和文檔
static_path = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=str(static_path)), name="static")

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


# 路由定義
# -----------------------------------------------------------------------------
@app.get("/")
async def root() -> FileResponse:
    """
    服務根路徑，返回前端應用的主頁面

    Returns:
        FileResponse: 返回靜態目錄中的 index.html 文件
    """
    return FileResponse(str(static_path / "index.html"))


# 註冊其他路由模組
# -----------------------------------------------------------------------------
# 文件上傳相關的路由（/upload/...）
app.include_router(upload.router)
# 數據查詢相關的路由（/query/...）
app.include_router(query.router)
