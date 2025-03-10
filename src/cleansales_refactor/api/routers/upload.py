import logging

import pandas as pd
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile
from sqlmodel import Session

from cleansales_refactor.core import Event, EventBus
from cleansales_refactor.services import CleanSalesService
from cleansales_refactor.shared.models import SourceData

from .. import ProcessEvent, get_event_bus, get_session
from ..models import ResponseModel

logger = logging.getLogger(__name__)


def get_clean_sales_service() -> CleanSalesService:
    return CleanSalesService()


router = APIRouter(prefix="/upload", tags=["upload"])


@router.post("/breeds", response_model=ResponseModel)
async def process_breeds_file(
    file_upload: UploadFile,
    check_exists: bool = Query(default=True, description="是否檢查是否已存在"),
    session: Session = Depends(get_session),
    service: CleanSalesService = Depends(get_clean_sales_service),
    event_bus: EventBus = Depends(get_event_bus),
) -> ResponseModel:
    try:
        if file_upload.filename is None:
            raise ValueError("未提供檔案名稱")
        if not file_upload.filename.endswith((".xlsx", ".xls")):
            raise ValueError("只接受 Excel 檔案 (.xlsx, .xls)")
        source_data = SourceData(
            file_name=file_upload.filename,
            dataframe=pd.read_excel(file_upload.file),
        )
        result = service.execute_clean_breeds(
            session, source_data, check_exists=check_exists
        )
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
        logger.error(f"處理入雛資料檔案時發生錯誤: {ve}")
        event_bus.publish(
            Event(
                event=ProcessEvent.BREEDS_PROCESSING_FAILED,
                content={"msg": str(ve)},
            )
        )
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
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
    file_upload: UploadFile,
    check_exists: bool = Query(default=True, description="是否檢查是否已存在"),
    session: Session = Depends(get_session),
    event_bus: EventBus = Depends(get_event_bus),
    service: CleanSalesService = Depends(get_clean_sales_service),
) -> ResponseModel:
    try:
        if file_upload.filename is None:
            raise ValueError("未提供檔案名稱")
        if not file_upload.filename.endswith((".xlsx", ".xls")):
            raise ValueError("只接受 Excel 檔案 (.xlsx, .xls)")
        source_data = SourceData(
            file_name=file_upload.filename,
            dataframe=pd.read_excel(file_upload.file),
        )
        result = service.execute_clean_sales(
            session, source_data, check_exists=check_exists
        )

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
        logger.error(f"處理販售資料檔案時發生錯誤: {ve}")
        event_bus.publish(
            Event(
                event=ProcessEvent.SALES_PROCESSING_FAILED,
                content={"msg": str(ve)},
            )
        )
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
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
