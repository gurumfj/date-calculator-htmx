import logging

from event_bus import Event
from fastapi import APIRouter, Depends, HTTPException, UploadFile

from ..core.events import ProcessEvent
from ..dependencies.api_dependency import PostApiDependency, get_api_dependency
from ..models.response import BatchAggregateResponseModel, ResponseModel

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/sales", tags=["sales"])


@router.post("/process", response_model=ResponseModel)
async def process_sales_file(
    file_upload: UploadFile,
    api_dependency: PostApiDependency = Depends(get_api_dependency),
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


@router.get("/sales/{batch_name}", response_model=BatchAggregateResponseModel)
async def get_sales_by_batch_name(
    batch_name: str,
    api_dependency: PostApiDependency = Depends(get_api_dependency),
) -> BatchAggregateResponseModel:
    return api_dependency.get_breeds_by_batch_name(batch_name)
