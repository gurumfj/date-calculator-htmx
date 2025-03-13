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
from typing import Any, Set

import pandas as pd
from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from pydantic import BaseModel
from sqlmodel import Session

from cleansales_refactor.core import Event, EventBus
from cleansales_refactor.services import CleanSalesService
from cleansales_refactor.shared.models import SourceData

from .. import ProcessEvent, get_event_bus, get_session

# from ..models import ResponseModel


class ResponseModel(BaseModel):
    """TODO: 需要重構"""

    status: str
    msg: str
    content: Any


# 配置路由器專用的日誌記錄器
logger = logging.getLogger(__name__)

# 添加允許的MIME類型
ALLOWED_MIME_TYPES: Set[str] = {
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",  # xlsx
    "application/vnd.ms-excel",  # xls
}

_clean_sales_service = CleanSalesService()


def get_clean_sales_service() -> CleanSalesService:
    """
    依賴注入：獲取清理銷售數據的服務實例

    Returns:
        CleanSalesService: 用於處理銷售和入雛數據的服務實例
    """
    return _clean_sales_service


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
    if file.filename is None:
        raise ValueError("未提供檔案名稱")

    content_type = file.content_type
    if content_type not in ALLOWED_MIME_TYPES:
        raise ValueError("只接受 Excel 檔案 (.xlsx, .xls)")


@router.post("/breeds", response_model=ResponseModel)
async def process_breeds_file(
    file_upload: UploadFile,
    check_exists: bool = Query(default=True, description="是否檢查是否已存在"),
    session: Session = Depends(get_session),
    service: CleanSalesService = Depends(get_clean_sales_service),
    event_bus: EventBus = Depends(get_event_bus),
) -> ResponseModel:
    """
    處理入雛資料 Excel 文件的上傳端點

    Args:
        file_upload (UploadFile): 上傳的 Excel 文件
        check_exists (bool): 是否檢查數據是否已存在
        session (Session): 數據庫會話實例
        service (CleanSalesService): 數據處理服務實例
        event_bus (EventBus): 事件總線實例

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
        result = service.execute_clean_breeds(
            session, source_data, check_exists=check_exists
        )

        # 處理成功時發布事件
        if result.status == "success":
            event_bus.publish(
                Event(
                    event=ProcessEvent.BREEDS_PROCESSING_COMPLETED,
                    content={"msg": result.msg},
                )
            )

        return ResponseModel(
            status=result.status,
            msg=result.msg,
            content=result.content,
        )

    except ValueError as ve:
        # 處理驗證錯誤
        logger.error(f"處理入雛資料檔案時發生錯誤: {ve}")
        event_bus.publish(
            Event(
                event=ProcessEvent.BREEDS_PROCESSING_FAILED,
                content={"msg": str(ve)},
            )
        )
        raise HTTPException(status_code=400, detail=str(ve))

    except Exception as e:
        # 處理其他未預期的錯誤
        logger.error(f"處理入雛資料檔案時發生錯誤: {e}")
        event_bus.publish(
            Event(
                event=ProcessEvent.BREEDS_PROCESSING_FAILED,
                content={
                    "msg": str(e),
                },
            )
        )
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sales", response_model=ResponseModel)
async def process_sales_file(
    file_upload: UploadFile = File(...),
    check_exists: bool = Query(default=True, description="是否檢查是否已存在"),
    session: Session = Depends(get_session),
    event_bus: EventBus = Depends(get_event_bus),
    service: CleanSalesService = Depends(get_clean_sales_service),
) -> ResponseModel:
    """
    處理銷售資料 Excel 文件的上傳端點

    Args:
        file_upload (UploadFile): 上傳的 Excel 文件
        check_exists (bool): 是否檢查數據是否已存在
        session (Session): 數據庫會話實例
        event_bus (EventBus): 事件總線實例
        service (CleanSalesService): 數據處理服務實例

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
        result = service.execute_clean_sales(
            session, source_data, check_exists=check_exists
        )

        # 處理成功時發布事件
        if result.status == "success":
            event_bus.publish(
                Event(
                    event=ProcessEvent.SALES_PROCESSING_COMPLETED,
                    content={"msg": result.msg},
                )
            )

        return ResponseModel(
            status=result.status,
            msg=result.msg,
            content=result.content,
        )

    except ValueError as ve:
        # 處理驗證錯誤
        logger.error(f"處理販售資料檔案時發生錯誤: {ve}")
        event_bus.publish(
            Event(
                event=ProcessEvent.SALES_PROCESSING_FAILED,
                content={"msg": str(ve)},
            )
        )
        raise HTTPException(status_code=400, detail=str(ve))

    except Exception as e:
        # 處理其他未預期的錯誤
        logger.error(f"處理販售資料檔案時發生錯誤: {e}")
        event_bus.publish(
            Event(
                event=ProcessEvent.SALES_PROCESSING_FAILED,
                content={
                    "msg": str(e),
                },
            )
        )
        raise HTTPException(status_code=500, detail=str(e))
