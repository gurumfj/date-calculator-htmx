"""
################################################################################
# 文件上傳路由模組
#
# 這個模組處理所有與文件上傳相關的 API 端點，包括：
# - 入雛資料文件上傳和處理
# - 銷售資料文件上傳和處理
#
# 主要功能：
# 1. 文件格式驗證（僅接受 Excel 文件）
# 2. 數據處理和清理
# 3. 事件發布（用於通知處理狀態）
# 4. 錯誤處理和日誌記錄
################################################################################
"""

import logging
from typing import Annotated

import pandas as pd
from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from sqlmodel import Session

from cleansales_backend.core import Event, EventBus
from cleansales_backend.processors import (
    BreedRecordProcessor,
    FeedRecordProcessor,
    IResponse,
    SaleRecordProcessor,
)
from cleansales_backend.services.query_service import QueryService
from cleansales_backend.shared.models import SourceData

from .. import ProcessEvent, core_db, get_event_bus
from .query import get_query_service

# from .. import batch_aggrs_cache

# 配置路由器專用的日誌記錄器
logger = logging.getLogger(__name__)


_sales_processor = SaleRecordProcessor()


def get_sales_processor() -> SaleRecordProcessor:
    return _sales_processor


_breeds_processor = BreedRecordProcessor()


def get_breeds_processor() -> BreedRecordProcessor:
    return _breeds_processor


_feeds_processor = FeedRecordProcessor()


def get_feeds_processor() -> FeedRecordProcessor:
    return _feeds_processor


# 創建路由器實例，設置前綴和標籤
router = APIRouter(prefix="/upload", tags=["upload"])


def validate_excel_file(file: UploadFile) -> None:
    """
    驗證上傳文件是否為有效的Excel文件

    Args:
        file (UploadFile): 上傳的文件

    Raises:
        ValueError: 當文件無效時拋出異常
    """
    allowed_mime_types: set[str] = {
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",  # xlsx
        "application/vnd.ms-excel",  # xls
    }
    if file.filename is None:
        raise ValueError("未提供檔案名稱")

    content_type = file.content_type
    if content_type not in allowed_mime_types:
        raise ValueError("只接受 Excel 檔案 (.xlsx, .xls)")


@router.post("/breeds", response_model=IResponse)
async def process_breeds_file(
    file_upload: Annotated[UploadFile, File(...)],
    session: Annotated[Session, Depends(core_db.get_session)],
    query_service: Annotated[QueryService, Depends(get_query_service)],
    processor: Annotated[BreedRecordProcessor, Depends(get_breeds_processor)],
    event_bus: Annotated[EventBus, Depends(get_event_bus)],
    check_exists: bool = Query(default=True, description="是否檢查是否已存在"),
) -> IResponse:
    """
    處理入雛資料 Excel 文件的上傳端點

    Args:
        file_upload (UploadFile): 上傳的 Excel 文件
        session (Session): 數據庫會話實例
        processor (BreedRecordProcessor): 數據處理服務實例
        event_bus (EventBus): 事件總線實例
        check_exists (bool): 是否檢查數據是否已存在

    Returns:
        ResponseModel: 包含處理結果的響應模型

    Raises:
        HTTPException: 當文件格式錯誤或處理過程中出現錯誤時
    """
    try:
        # 使用新的驗證函數
        validate_excel_file(file_upload)

        # 讀取並轉換數據
        source_data = SourceData(
            # 使用空字符串作為默認值，確保文件名不為 None
            file_name=file_upload.filename or "",
            dataframe=pd.read_excel(file_upload.file),
        )

        # 執行數據處理
        result = processor.execute(session, source_data, check_md5=check_exists)

        # 處理成功時發布事件
        if result.success:
            # batch_aggrs_cache.invalidate()
            query_service.cache_clear()
            event_bus.publish(
                Event(
                    event=ProcessEvent.BREEDS_PROCESSING_COMPLETED,
                    message="處理入雛資料檔案成功",
                    content=result.content,
                )
            )

        return result

    except ValueError as ve:
        # 處理驗證錯誤
        logger.error(f"處理入雛資料檔案時發生錯誤: {ve}")
        event_bus.publish(
            Event(
                event=ProcessEvent.BREEDS_PROCESSING_FAILED,
                message="處理入雛資料檔案時發生錯誤",
                content={"error": str(ve)},
            )
        )
        raise HTTPException(status_code=400, detail=str(ve))

    except Exception as e:
        # 處理其他未預期的錯誤
        logger.error(f"處理入雛資料檔案時發生錯誤: {e}")
        event_bus.publish(
            Event(
                event=ProcessEvent.BREEDS_PROCESSING_FAILED,
                message="處理入雛資料檔案時發生錯誤",
                content={
                    "error": str(e),
                },
            )
        )
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sales", response_model=IResponse)
async def process_sales_file(
    file_upload: Annotated[UploadFile, File(...)],
    session: Annotated[Session, Depends(core_db.get_session)],
    query_service: Annotated[QueryService, Depends(get_query_service)],
    event_bus: Annotated[EventBus, Depends(get_event_bus)],
    processor: Annotated[SaleRecordProcessor, Depends(get_sales_processor)],
    check_exists: bool = Query(default=True, description="是否檢查是否已存在"),
) -> IResponse:
    """
    處理銷售資料 Excel 文件的上傳端點

    Args:
        session (Session): 數據庫會話實例
        event_bus (EventBus): 事件總線實例
        processor (SaleRecordProcessor): 數據處理服務實例
        file_upload (UploadFile): 上傳的 Excel 文件
        check_exists (bool): 是否檢查數據是否已存在

    Returns:
        ResponseModel: 包含處理結果的響應模型

    Raises:
        HTTPException: 當文件格式錯誤或處理過程中出現錯誤時
    """
    try:
        # 使用新的驗證函數
        validate_excel_file(file_upload)

        # 讀取並轉換數據
        source_data = SourceData(
            # 使用空字符串作為默認值，確保文件名不為 None
            file_name=file_upload.filename or "",
            dataframe=pd.read_excel(file_upload.file),
        )

        # 執行數據處理
        result = processor.execute(session, source_data, check_md5=check_exists)

        # 處理成功時發布事件
        if result.success:
            # batch_aggrs_cache.invalidate()
            query_service.cache_clear()
            event_bus.publish(
                Event(
                    event=ProcessEvent.SALES_PROCESSING_COMPLETED,
                    message="處理販售資料檔案成功",
                    content=result.content,
                )
            )

        return result

    except ValueError as ve:
        # 處理驗證錯誤
        logger.error(f"處理販售資料檔案時發生錯誤: {ve}")
        event_bus.publish(
            Event(
                event=ProcessEvent.SALES_PROCESSING_FAILED,
                message="處理販售資料檔案時發生錯誤",
                content={"error": str(ve)},
            )
        )
        raise HTTPException(status_code=400, detail=str(ve))

    except Exception as e:
        # 處理其他未預期的錯誤
        logger.error(f"處理販售資料檔案時發生錯誤: {e}")
        event_bus.publish(
            Event(
                event=ProcessEvent.SALES_PROCESSING_FAILED,
                message="處理販售資料檔案時發生錯誤",
                content={
                    "error": str(e),
                },
            )
        )
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/feeds", response_model=IResponse)
async def process_feeds_file(
    file_upload: Annotated[UploadFile, File(...)],
    session: Annotated[Session, Depends(core_db.get_session)],
    query_service: Annotated[QueryService, Depends(get_query_service)],
    event_bus: Annotated[EventBus, Depends(get_event_bus)],
    processor: Annotated[FeedRecordProcessor, Depends(get_feeds_processor)],
    check_exists: bool = Query(default=True, description="是否檢查是否已存在"),
) -> IResponse:
    """
    處理飼料記錄 Excel 文件的上傳端點

    Args:
        file_upload (UploadFile): 上傳的 Excel 文件
        session (Session): 數據庫會話實例
        event_bus (EventBus): 事件總線實例
        processor (FeedRecordProcessor): 數據處理服務實例
        check_exists (bool): 是否檢查數據是否已存在

    Returns:
        ResponseModel: 包含處理結果的響應模型

    Raises:
        HTTPException: 當文件格式錯誤或處理過程中出現錯誤時
    """
    try:
        # 使用新的驗證函數
        validate_excel_file(file_upload)

        # 讀取並轉換數據
        source_data = SourceData(
            # 使用空字符串作為默認值，確保文件名不為 None
            file_name=file_upload.filename or "",
            dataframe=pd.read_excel(file_upload.file),
        )

        # 執行數據處理
        result = processor.execute(session, source_data, check_md5=check_exists)

        # 處理成功時發布事件
        if result.success:
            # batch_aggrs_cache.invalidate()
            query_service.cache_clear()
            event_bus.publish(
                Event(
                    event=ProcessEvent.FEEDS_PROCESSING_COMPLETED,
                    message="處理飼料記錄檔案成功",
                    content=result.content,
                )
            )
        return result
    except ValueError as ve:
        # 處理驗證錯誤
        logger.error(f"處理飼料記錄檔案時發生錯誤: {ve}")
        event_bus.publish(
            Event(
                event=ProcessEvent.FEEDS_PROCESSING_FAILED,
                message="處理飼料記錄檔案時發生錯誤",
                content={"error": str(ve)},
            )
        )
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        # 處理其他未預期的錯誤
        logger.error(f"處理飼料記錄檔案時發生錯誤: {e}")
        event_bus.publish(
            Event(
                event=ProcessEvent.FEEDS_PROCESSING_FAILED,
                message="處理飼料記錄檔案時發生錯誤",
                content={
                    "error": str(e),
                },
            )
        )
        raise HTTPException(status_code=500, detail=str(e))
