import logging
from typing import TYPE_CHECKING

from fastapi import APIRouter, Depends, HTTPException, UploadFile

from cleansales_refactor.core.event_bus import Event

from ..core.dependencies import get_api_dependency
from ..core.events import ProcessEvent
from ..models.response import ResponseModel

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/upload", tags=["upload"])


@router.post("/breeds", response_model=ResponseModel)
async def process_breeds_file(
    file_upload: UploadFile,
    api_dependency=Depends(get_api_dependency),
) -> ResponseModel:
    try:
        if file_upload.filename is None:
            raise ValueError("未提供檔案名稱")
        if not file_upload.filename.endswith((".xlsx", ".xls")):
            raise ValueError("只接受 Excel 檔案 (.xlsx, .xls)")
        result: ResponseModel = api_dependency.breed_processpipline(file_upload)
        return result
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        logger.error(f"處理入雛資料檔案時發生錯誤: {e}")
        api_dependency.event_bus.publish(
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
    api_dependency=Depends(get_api_dependency),
) -> ResponseModel:
    try:
        if file_upload.filename is None:
            raise ValueError("未提供檔案名稱")
        if not file_upload.filename.endswith((".xlsx", ".xls")):
            raise ValueError("只接受 Excel 檔案 (.xlsx, .xls)")
        result: ResponseModel = api_dependency.sales_processpipline(file_upload)
        return result
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        logger.error(f"處理販售資料檔案時發生錯誤: {e}")
        api_dependency.event_bus.publish(
            Event(
                event=ProcessEvent.SALES_PROCESSING_FAILED,
                content={
                    "msg": str(e),
                },
            )
        )
        raise HTTPException(status_code=500, detail=str(e))
