import io
import logging
from typing import Any, Dict

import pandas as pd
from fastapi import FastAPI, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from cleansales_refactor.processor import SalesProcessor

# 設定 logger
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)

logger = logging.getLogger(__name__)

app = FastAPI(
    title="銷售資料處理 API",
    description="""
    提供銷售資料處理服務的 API
    
    ## 功能
    - 上傳 Excel 檔案進行處理
    - 支援 .xlsx 和 .xls 格式
    - 返回處理結果和錯誤訊息
    
    ## 使用方式
    1. 使用 POST `/process-sales` 上傳 Excel 檔案
    2. 系統會自動處理檔案並返回結果
    """,
    version="1.0.0",
)

# 設定 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 在生產環境中應該限制來源
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root() -> Dict[str, str]:
    """API 根路由

    Returns:
        包含 API 資訊的字典
    """
    return {
        "message": "歡迎使用銷售資料處理 API",
        "docs_url": "/docs",
        "redoc_url": "/redoc",
    }


def process_excel_file(file_content: bytes) -> Dict[str, Any]:
    """處理 Excel 檔案內容並返回處理結果"""
    try:
        # 讀取 Excel 檔案到 DataFrame
        df = pd.read_excel(io.BytesIO(file_content))

        # 初始化 SalesProcessor
        processor = SalesProcessor()

        # 處理數據
        result = processor.process_data(df)

        # 將結果轉換為簡單的統計數據
        serializable_result = {
            "success": True,
            "processed_count": len(result.processed_data),
            "error_count": len(result.errors) if result.errors else 0,
        }

        return serializable_result
    except Exception as e:
        logger.error(f"處理檔案時發生錯誤: {str(e)}")
        return {"success": False, "error": str(e)}


@app.post("/process-sales")
async def process_sales_file(file: UploadFile) -> JSONResponse:
    """處理上傳的銷售資料檔案

    Args:
        file: 上傳的 Excel 檔案

    Returns:
        包含處理結果的 JSON 回應

    Raises:
        HTTPException: 當檔案格式不正確或處理過程發生錯誤時
    """
    if file.filename is None:
        raise HTTPException(status_code=400, detail="未提供檔案名稱")
    if not file.filename.endswith((".xlsx", ".xls")):
        raise HTTPException(status_code=400, detail="只接受 Excel 檔案 (.xlsx, .xls)")

    try:
        # 讀取檔案內容
        file_content = await file.read()
        # 處理檔案
        result = process_excel_file(file_content)

        return JSONResponse(content=result)
    except Exception as e:
        logger.error(f"處理檔案時發生錯誤: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "api:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        reload_dirs=["src"],
    )
