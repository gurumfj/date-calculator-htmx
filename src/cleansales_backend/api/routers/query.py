"""
################################################################################
# 數據查詢路由模組
#
# 這個模組提供了所有與數據查詢相關的 API 端點，包括：
# - 未結案批次查詢
# - 特定批次查詢
# - 銷售記錄查詢
#
# 主要功能：
# 1. 數據查詢和過濾
# 2. 數據轉換（DTO 轉換）
# 3. 錯誤處理和日誌記錄
# 4. 分頁支持
################################################################################
"""

import logging
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, HTTPException, Query

from cleansales_backend.domain.models.batch_aggregate import BatchAggregateModel
from cleansales_backend.domain.models.sales_pivot import SalesPivotModel
from cleansales_backend.domain.models.sales_summary import SalesSummaryModel
from cleansales_backend.processors import BreedRecordProcessor, SaleRecordProcessor
from cleansales_backend.services import QueryService

from .. import core_db

# from .. import batch_aggrs_cache
from ..models import ContextModel, ResponseModel

# 配置查詢路由器專用的日誌記錄器
logger = logging.getLogger(__name__)


# 創建路由器實例，設置前綴和標籤
router = APIRouter(prefix="/api", tags=["api"])

_breed_repository = BreedRecordProcessor()
_sale_repository = SaleRecordProcessor()
_query_service = QueryService(
    _breed_repository,
    _sale_repository,
    core_db,
)


def get_query_service() -> QueryService:
    """依賴注入：獲取查詢服務實例

    Returns:
        QueryService: 查詢服務實例
    """
    return _query_service


@router.get(
    "/not-completed",
    response_model=ResponseModel[BatchAggregateModel],
    response_model_exclude_unset=True,
    response_model_exclude_none=True,
)
async def get_not_completed_batches(
    query_service: Annotated[QueryService, Depends(get_query_service)],
) -> ResponseModel[BatchAggregateModel]:
    """獲取未結案的批次列表

    Args:
        query_service (QueryService): 查詢服務實例

    Returns:
        Response[BatchAggregateModel]: 包含未結案批次列表的響應
    """
    try:
        aggrs = query_service.get_batch_aggregates()
        data = query_service.get_not_completed_batches_summary(aggrs)
        return ResponseModel(
            success=True if data else False,
            message=f"獲取{len(data)}筆未結案批次" if data else "未找到未結案批次",
            content=ContextModel(
                data=[BatchAggregateModel.create_from(aggr) for aggr in data]
            ),
        )
    except Exception as e:
        logger.error(f"獲取未結案批次時發生錯誤: {e}")
        raise HTTPException(
            status_code=500, detail={"error": str(e), "type": type(e).__name__}
        )


@router.get(
    "/batch",
    response_model=ResponseModel[BatchAggregateModel],
    response_model_exclude_unset=True,
    response_model_exclude_none=True,
)
async def get_batch_aggregates_by_criteria(
    query_service: Annotated[QueryService, Depends(get_query_service)],
    batch_name: str | None = Query(
        default=None,
        description="批次名稱。空列表或 None 表示不過濾批次名稱",
    ),
    breed_type: Literal["黑羽", "古早", "舍黑", "閹雞"] | None = Query(
        default=None,
        description="可包含多個雞種。空列表或 None 表示不過濾雞種",
    ),
    batch_status: list[Literal["completed", "breeding", "sale"]] | None = Query(
        default=None,
        description="可包含多個狀態。空列表或 None 表示不過濾狀態",
    ),
) -> ResponseModel[BatchAggregateModel]:
    """獲取特定批次名稱的批次聚合列表

    Args:
        batch_name (str): 批次名稱
        breed_type (Literal["黑羽", "古早", "舍黑", "閹雞"]): 雏種類型
        batch_status (list[Literal["completed", "breeding", "sale"]]): 批次狀態
        query_service (QueryService): 查詢服務實例

    Returns:
        Response[BatchAggregateModel]: 包含特定批次名稱的批次聚合列表的響應
    """
    try:
        # if batch_state:=status:
        batch_status_set = set(batch_status) if batch_status is not None else None

        aggrs = query_service.get_batch_aggregates()
        filtered_aggrs = query_service.get_batch_aggregates_by_criteria(
            aggrs, batch_name, breed_type, batch_status_set
        )
        return ResponseModel(
            success=True if filtered_aggrs else False,
            message=f"獲取{len(filtered_aggrs)}筆批次聚合"
            if filtered_aggrs
            else "未找到批次聚合",
            content=ContextModel(
                data=[BatchAggregateModel.create_from(aggr) for aggr in filtered_aggrs]
            ),
            errors=[
                {
                    "batch_name": batch_name,
                    "breed_type": breed_type,
                    "batch_status": batch_status,
                }
            ]
            if not filtered_aggrs
            else None,
        )
    except Exception as e:
        logger.error(f"獲取批次聚合時發生錯誤: {e}")
        raise HTTPException(
            status_code=500, detail={"error": str(e), "type": type(e).__name__}
        )


@router.get(
    "/salesummary",
    deprecated=True,
    description="請使用 /batch 路由",
    response_model=ResponseModel[SalesSummaryModel],
    response_model_exclude_unset=True,
    response_model_exclude_none=True,
)
async def get_sales_summary(
    query_service: Annotated[QueryService, Depends(get_query_service)],
    batch_name: str | None = Query(
        default=None,
        description="批次名稱。空列表或 None 表示不過濾批次名稱",
    ),
) -> ResponseModel[SalesSummaryModel]:
    """獲取特定批次名稱的批次聚合列表

    Args:
        batch_name (str): 批次名稱
        query_service (QueryService): 查詢服務實例

    Returns:
        Response[BatchAggregateModel]: 包含特定批次名稱的批次聚合列表的響應
    """
    try:
        # if batch_state:=status:

        aggrs = query_service.get_batch_aggregates()
        filtered_aggrs = query_service.get_batch_aggregates_by_criteria(
            aggrs, batch_name=batch_name
        )
        sales_summarys = [
            SalesSummaryModel.create_from(aggr.sales_summary)
            for aggr in filtered_aggrs
            if aggr.sales_summary
        ]
        return ResponseModel(
            success=True if filtered_aggrs else False,
            message=f"獲取{len(filtered_aggrs)}筆批次聚合"
            if filtered_aggrs
            else "未找到批次聚合",
            content=ContextModel(data=sales_summarys),
            errors=[
                {
                    "batch_name": batch_name,
                }
            ]
            if not filtered_aggrs
            else None,
        )
    except Exception as e:
        logger.error(f"獲取批次聚合時發生錯誤: {e}")
        raise HTTPException(
            status_code=500, detail={"error": str(e), "type": type(e).__name__}
        )


@router.get(
    "/sales_pivot",
    response_model=ResponseModel[SalesPivotModel],
    response_model_exclude_unset=True,
    response_model_exclude_none=True,
)
async def get_sales_pivot(
    query_service: Annotated[QueryService, Depends(get_query_service)],
    batch_name: str | None = Query(
        default=None,
        description="批次名稱。空列表或 None 表示不過濾批次名稱",
    ),
) -> ResponseModel[SalesPivotModel]:
    """
    獲取特定批次名稱的銷售走勢資料

    Args:
        batch_name (str | None): 批次名稱。空列表或 None 表示不過濾批次名稱
        query_service (QueryService): 查詢服務實例

    Returns:
        Response[SalesPivotModel]: 包含特定批次名稱的銷售走勢資料的響應
    """
    try:
        # 取得所有批次聚合
        aggrs = query_service.get_batch_aggregates()

        # 將批次聚合以批次名稱為條件進行過濾
        filtered_aggrs = query_service.get_batch_aggregates_by_criteria(
            aggrs, batch_name=batch_name
        )

        # 將過濾後的批次聚合轉換為銷售走勢資料
        sales_pivots = [
            aggr.sales_summary.sales_pivot.to_dto()
            for aggr in filtered_aggrs
            if aggr.sales_summary
        ]

        # 將結果轉換為 ResponseModel
        return ResponseModel(
            success=True if filtered_aggrs else False,
            message=f"獲取{len(filtered_aggrs)}筆批次聚合"
            if filtered_aggrs
            else "未找到批次聚合",
            content=ContextModel(data=sales_pivots),
            errors=[
                {
                    "batch_name": batch_name,
                }
            ]
            if not filtered_aggrs
            else None,
        )
    except Exception as e:
        # 如果發生錯誤，則日誌記錄錯誤並將錯誤訊息傳回客戶端
        logger.error(f"獲取批次聚合時發生錯誤: {e}")
        raise HTTPException(
            status_code=500, detail={"error": str(e), "type": type(e).__name__}
        )
