import logging
from typing import Any, Callable, Dict

import pandas as pd
from fastapi import FastAPI, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from cleansales_refactor.exporters.sales_exporter import SaleSQLiteExporter
from cleansales_refactor.models.shared import ProcessingResult, SourceData
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


# def process_excel_file(file_content: bytes) -> Dict[str, Any]:
#     """處理 Excel 檔案內容並返回處理結果"""
#     try:
#         reader = create_bytes_reader(file_content)
#         processor = create_data_processor(SalesProcessor())
#         exporter = create_data_exporter(SaleSQLiteExporter("api_test.db"))
#         # 處理數據

#         result = exporter(processor(reader()))

#         # 將結果轉換為簡單的統計數據
#         # serializable_result = result.to_dict()

#         return result
#     except Exception as e:
#         logger.error(f"處理檔案時發生錯誤: {str(e)}")
#         return {"success": False, "error": str(e)}


@app.post("/process-sales")
async def process_sales_file(file_upload: UploadFile) -> JSONResponse:
    """處理上傳的銷售資料檔案

    Args:
        file_upload: 包含上傳的 Excel 檔案的 Pydantic 模型

    Returns:
        包含處理結果的 JSON 回應

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

        df = pd.read_excel(file_upload.file)

        source_data = SourceData(file_name=file_upload.filename, dataframe=df)
        processor: Callable[[pd.DataFrame], ProcessingResult[Any]] = (
            lambda df: SalesProcessor.process_data(df)
        )
        exporter: Callable[[ProcessingResult[Any]], dict[str, Any]] = (
            lambda result: SaleSQLiteExporter("src/api_test.db").export_data(
                source_data, result
            )
        )
        process_pipeline: Callable[[], dict[str, Any]] = lambda: exporter(
            processor(source_data.dataframe)
        )

        result = process_pipeline()

        return JSONResponse(content=result)
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
