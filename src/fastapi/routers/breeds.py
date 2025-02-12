import logging
import traceback

from event_bus import Event
from fastapi import APIRouter, Depends, HTTPException, UploadFile

from ..core.events import ProcessEvent
from ..dependencies.api_dependency import PostApiDependency, get_api_dependency
from ..models.response import BatchAggregateResponseModel, ResponseModel

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/breeds", tags=["breeds"])


@router.post("/process", response_model=ResponseModel)
async def process_breeds_file(
    file_upload: UploadFile,
    api_dependency: PostApiDependency = Depends(get_api_dependency),
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


@router.get("/not-completed", response_model=BatchAggregateResponseModel)
async def get_breeding_data(
    api_dependency: PostApiDependency = Depends(get_api_dependency),
) -> BatchAggregateResponseModel:
    """取得未結案的入雛批次資料

    Returns:
        BatchAggregateResponseModel: {
            "status": "success",
            "msg": "處理訊息",
            "content": {
                "count": 批次總數,
                "batches": [
                    {
                        "batch_name": "批次名稱",
                        "farm_name": "農場名稱",
                        "address": "地址",
                        "farmer_name": "場主名稱",
                        "total_male": "公雞總數",
                        "total_female": "母雞總數",
                        "veterinarian": "獸醫",
                        "batch_state": "批次狀態(養殖中/銷售中/結案)",
                        "breed_date": ["入雛日期"],
                        "supplier": ["種母場"],
                        "chicken_breed": ["雞種"],
                        "male": [公雞數量],
                        "female": [母雞數量],
                        "day_age": [日齡],
                        "week_age": ["週齡"]
                    }
                ]
            }
        }

    Raises:
        HTTPException:
            - 500: 伺服器內部錯誤，包含詳細錯誤訊息
    """
    try:
        return api_dependency.get_breeds_is_not_completed()
    except Exception as e:
        error_msg = f"取得未結場入雛資料時發生錯誤: {str(e)}\n"
        error_msg += f"錯誤類型: {type(e).__name__}\n"
        error_msg += f"堆疊追蹤:\n{traceback.format_exc()}"
        logger.error(error_msg)
        raise HTTPException(
            status_code=500,
            detail={
                "error": str(e),
                "type": type(e).__name__,
                "traceback": traceback.format_exc(),
            },
        )
