import logging
from enum import Enum
from typing import Any, Callable, Dict

import pandas as pd
from fastapi import FastAPI, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import Session, SQLModel, select

from cleansales_refactor.exporters import (
    BreedRecordORM,
    BreedSQLiteExporter,
    Database,
    SaleSQLiteExporter,
)
from cleansales_refactor.models.shared import ProcessingResult, SourceData
from cleansales_refactor.processor import BreedsProcessor, SalesProcessor
from event_bus import Event, EventBus, TelegramNotifier

# 先設定基本的 logging 配置
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)

# 設定特定的 processor logger
processor_logger = logging.getLogger("cleansales_refactor.processor")
processor_logger.setLevel(logging.DEBUG)
# 確保 handler 也設定正確的層級
for handler in processor_logger.handlers:
    handler.setLevel(logging.DEBUG)

# API logger
logger = logging.getLogger(__name__)


class ResponseModel(SQLModel):
    status: str
    msg: str
    content: dict[str, Any]


class PostApiDependency:
    def __init__(self, event_bus: EventBus) -> None:
        self.sales_exporter = SaleSQLiteExporter()
        self.breed_exporter = BreedSQLiteExporter()
        self.event_bus = event_bus

    def sales_processpipline(
        self, upload_file: UploadFile, session: Session
    ) -> ResponseModel:
        source_data = SourceData(
            file_name=upload_file.filename or "",
            dataframe=pd.read_excel(upload_file.file),
        )
        processor: Callable[[SourceData], ProcessingResult[Any]] = (
            lambda source_data: SalesProcessor.execute(source_data)
        )
        exporter: Callable[[ProcessingResult[Any]], dict[str, Any]] = (
            lambda processed_data: self.sales_exporter.execute(session, processed_data)
        )
        is_exists: Callable[[SourceData], bool] = (
            lambda x: self.sales_exporter.is_source_md5_exists_in_latest_record(
                session, x
            )
        )

        if is_exists(source_data):
            logger.debug(f"販售資料 md5 {source_data.md5} 已存在")
            return ResponseModel(status="error", msg="販售資料已存在", content={})
        else:
            result = exporter(processor(source_data))
            return ResponseModel(
                status="success",
                msg=f"成功匯入販售資料 {result['added']} 筆資料，刪除 {result['deleted']} 筆資料，無法驗證資料 {result['unvalidated']} 筆",
                content=result,
            )

    def breed_processpipline(
        self, upload_file: UploadFile, session: Session
    ) -> ResponseModel:
        source_data = SourceData(
            file_name=upload_file.filename or "",
            dataframe=pd.read_excel(upload_file.file),
        )
        processor: Callable[[SourceData], ProcessingResult[Any]] = (
            lambda source_data: BreedsProcessor.execute(source_data)
        )
        exporter: Callable[[ProcessingResult[Any]], dict[str, Any]] = (
            lambda processed_data: self.breed_exporter.execute(session, processed_data)
        )
        is_exists: Callable[[SourceData], bool] = (
            lambda x: self.breed_exporter.is_source_md5_exists_in_latest_record(
                session, x
            )
        )

        if is_exists(source_data):
            logger.debug(f"入雛資料 md5 {source_data.md5} 已存在")
            return ResponseModel(status="error", msg="入雛資料已存在", content={})
        else:
            result = exporter(processor(source_data))
            return ResponseModel(
                status="success",
                msg=f"成功匯入入雛資料 {result['added']} 筆資料，刪除 {result['deleted']} 筆資料，無法驗證資料 {result['unvalidated']} 筆",
                content=result,
            )

    def get_breeds_is_not_completed(self, session: Session) -> ResponseModel:
        stmt = (
            select(BreedRecordORM)
            .where(
                (BreedRecordORM.is_completed != "結場")
                | (BreedRecordORM.is_completed.is_(None))
            )
            .order_by(BreedRecordORM.breed_date.desc())
        )
        breeds = session.exec(stmt).all()
        return ResponseModel(
            status="success",
            msg=f"成功取得未結場入雛資料 {len(breeds)} 筆",
            content={
                "breeds": [breed.model_dump() for breed in breeds],
            },
        )


class ProcessEvent(Enum):
    SALES_PROCESSING_STARTED = "sales_processing_started"
    SALES_PROCESSING_COMPLETED = "sales_processing_completed"
    SALES_PROCESSING_FAILED = "sales_processing_failed"

    BREEDS_PROCESSING_STARTED = "breeds_processing_started"
    BREEDS_PROCESSING_COMPLETED = "breeds_processing_completed"
    BREEDS_PROCESSING_FAILED = "breeds_processing_failed"


db = Database("data/cleansales.db")
event_bus = EventBus.get_instance()
telegram_notifier = TelegramNotifier(
    event_bus,
    [
        ProcessEvent.SALES_PROCESSING_STARTED,
        ProcessEvent.SALES_PROCESSING_COMPLETED,
        ProcessEvent.SALES_PROCESSING_FAILED,
        ProcessEvent.BREEDS_PROCESSING_STARTED,
        ProcessEvent.BREEDS_PROCESSING_COMPLETED,
        ProcessEvent.BREEDS_PROCESSING_FAILED,
    ],
)
api_function = PostApiDependency(event_bus)

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


@app.post("/process-sales", response_model=ResponseModel)
async def process_sales_file(
    file_upload: UploadFile,
) -> ResponseModel:
    """處理上傳的銷售資料檔案

    Args:
        file_upload: 包含上傳的 Excel 檔案的 Pydantic 模型

    Returns:
        包含處理結果的字典

    Raises:
        HTTPException: 當檔案格式不正確或處理過程發生錯誤時
    """
    with db.get_session() as session:
        try:
            # 讀取檔案內容
            if file_upload.filename is None:
                raise ValueError("未提供檔案名稱")
            if not file_upload.filename.endswith((".xlsx", ".xls")):
                raise ValueError("只接受 Excel 檔案 (.xlsx, .xls)")
            # 處理檔案
            result: ResponseModel = api_function.sales_processpipline(
                file_upload, session
            )
            event_bus.publish(
                Event(
                    event=ProcessEvent.SALES_PROCESSING_COMPLETED,
                    content={
                        "result": result,
                    },
                    metadata={},
                )
            )
            return result
        except ValueError as ve:
            event_bus.publish(
                Event(
                    event=ProcessEvent.SALES_PROCESSING_FAILED,
                    content={
                        "message": str(ve),
                    },
                    metadata={},
                )
            )
            raise HTTPException(status_code=400, detail=str(ve))
        except Exception as e:
            event_bus.publish(
                Event(
                    event=ProcessEvent.SALES_PROCESSING_FAILED,
                    content={
                        "message": str(e),
                    },
                    metadata={},
                )
            )
            logger.error(f"處理檔案時發生錯誤: {e}")
            raise HTTPException(status_code=500, detail=str(e))


@app.post("/process-breeds", response_model=ResponseModel)
async def process_breeds_file(
    file_upload: UploadFile,
) -> ResponseModel:
    with db.get_session() as session:
        try:
            if file_upload.filename is None:
                raise ValueError("未提供檔案名稱")
            if not file_upload.filename.endswith((".xlsx", ".xls")):
                raise ValueError("只接受 Excel 檔案 (.xlsx, .xls)")
            result: ResponseModel = api_function.breed_processpipline(
                file_upload, session
            )
            event_bus.publish(
                Event(
                    event=ProcessEvent.BREEDS_PROCESSING_COMPLETED,
                    content={
                        "result": result,
                    },
                    metadata={},
                )
            )
            return result
        except ValueError as ve:
            raise HTTPException(status_code=400, detail=str(ve))
        except Exception as e:
            logger.error(f"處理檔案時發生錯誤: {e}")
            raise HTTPException(status_code=500, detail=str(e))


@app.get("/breeding", response_model=ResponseModel)
async def get_breeding_data() -> ResponseModel:
    with db.get_session() as session:
        try:
            return api_function.get_breeds_is_not_completed(session)
        except Exception as e:
            logger.error(f"取得未結場入雛資料時發生錯誤: {e}")
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
