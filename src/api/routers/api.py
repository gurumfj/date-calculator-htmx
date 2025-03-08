import logging
import traceback

from fastapi import APIRouter, Depends, HTTPException

from ..dependencies.api_dependency import PostApiDependency, get_api_dependency
from ..models.response import BatchAggregateResponseModel

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["api"])


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

@router.get("/{batch_name}", response_model=BatchAggregateResponseModel)
async def get_sales_by_batch_name(
    batch_name: str,
    api_dependency: PostApiDependency = Depends(get_api_dependency),
) -> BatchAggregateResponseModel:
    return api_dependency.get_breeds_by_batch_name(batch_name)
