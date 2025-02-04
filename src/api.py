import logging
from typing import Any, Callable, Dict

import pandas as pd
from fastapi import Depends, FastAPI, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlmodel import Session

from cleansales_refactor.exporters import Database, SaleSQLiteExporter
from cleansales_refactor.models.shared import ProcessingResult, SourceData
from cleansales_refactor.processor import SalesProcessor

# 設定 logger
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)

logger = logging.getLogger(__name__)

db = Database("data/cleansales_dev.db")


def sales_processpipline(upload_file: UploadFile, session: Session) -> dict[str, Any]:
    source_data = SourceData(
        file_name=upload_file.filename or "",
        dataframe=pd.read_excel(upload_file.file),
    )
    processor: Callable[[pd.DataFrame], ProcessingResult[Any]] = (
        lambda df: SalesProcessor.process_data(df)
    )
    exporter: Callable[[ProcessingResult[Any]], dict[str, Any]] = (
        lambda processed_data: SaleSQLiteExporter(session).export_data(
            source_data, processed_data
        )
    )
    is_exists: Callable[[str], bool] = lambda x: SaleSQLiteExporter(
        session
    ).is_source_md5_exists_in_latest_record(x)

    if is_exists(source_data.md5):
        return {"status": "error", "msg": "md5 已存在"}
    else:
        return exporter(processor(source_data.dataframe))


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


@app.post("/process-sales")
async def process_sales_file(
    file_upload: UploadFile,
    session: Session = Depends(db.get_session),
) -> JSONResponse:
    """處理上傳的銷售資料檔案

    Args:
        file_upload: 包含上傳的 Excel 檔案的 Pydantic 模型

    Returns:
        包含處理結果的字典

    Raises:
        HTTPException: 當檔案格式不正確或處理過程發生錯誤時
    """
    try:
        # 讀取檔案內容
        if file_upload.filename is None:
            raise ValueError("未提供檔案名稱")
        if not file_upload.filename.endswith((".xlsx", ".xls")):
            raise ValueError("只接受 Excel 檔案 (.xlsx, .xls)")
        # 處理檔案
        result: dict[str, Any] = sales_processpipline(file_upload, session)
        return JSONResponse(result)
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
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
