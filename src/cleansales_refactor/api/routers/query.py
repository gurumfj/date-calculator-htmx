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
import traceback
from typing import Any, Dict, List, Literal

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlmodel import Session

from cleansales_refactor.repositories import BreedRepository, SaleRepository
from cleansales_refactor.services import QueryService

from .. import get_session
from ..models import (
    BatchAggregateResponseModel,
)
from ..services import DTOService

# 配置查詢路由器專用的日誌記錄器
logger = logging.getLogger(__name__)

# 創建路由器實例，設置前綴和標籤
router = APIRouter(prefix="/api", tags=["api"])

_breed_repository = BreedRepository()
_sale_repository = SaleRepository()
_query_service = QueryService(
    _breed_repository,
    _sale_repository,
)


def get_query_service() -> QueryService:
    """依賴注入：獲取查詢服務實例

    Args:
        session (Session): 數據庫會話實例

    Returns:
        QueryService: 查詢服務實例
    """
    return _query_service


class BatchStatisticsResponse(BaseModel):
    """批次統計響應模型"""

    batch_info: Dict[str, Any]
    totals: Dict[str, Any]
    customer_statistics: Dict[str, Dict[str, float]]
    sales_trends: Dict[str, List[Dict[str, Any]]]


@router.get("/not-completed", response_model=List[BatchAggregateResponseModel])
async def get_not_completed_batches(
    session: Session = Depends(get_session),
    query_service: QueryService = Depends(get_query_service),
) -> List[BatchAggregateResponseModel]:
    """獲取未結案的批次列表

    Args:
        query_service (QueryService): 查詢服務實例

    Returns:
        List[BatchAggregateResponseModel]: 未結案的批次列表
    """
    try:
        filtered_aggrs = query_service.get_filtered_aggregates(
            session, status=["breeding", "sale"]
        )
        return [DTOService.batch_aggregate_to_dto(batch) for batch in filtered_aggrs]
    except Exception as e:
        logger.error(f"獲取未結案批次時發生錯誤: {str(e)}\n{traceback.format_exc()}")
        raise HTTPException(
            status_code=500, detail={"error": str(e), "type": type(e).__name__}
        )


# api for query batch aggregate in specific batch name
@router.get("/query/batch", response_model=List[BatchAggregateResponseModel])
async def get_batch_aggregate_by_name(
    batch_name: str | None = None,
    breed_type: Literal["黑羽", "古早", "舍黑", "閹雞"] | None = Query(
        default=None,
        description="雞種類型，可包含多個雞種(黑羽, 古早, 舍黑, 閹雞)。空列表或 None 表示不過濾雞種",
    ),
    status: list[Literal["all", "completed", "breeding", "sale"]] | None = Query(
        default=["all"],
        description="批次狀態，可包含多個狀態(all, completed, breeding, sale)。空列表或 ['all'] 表示不過濾狀態",
    ),
    session: Session = Depends(get_session),
    query_service: QueryService = Depends(get_query_service),
) -> List[BatchAggregateResponseModel]:
    """獲取特定批次名稱的批次聚合列表

    Args:
        batch_name (str): 批次名稱
        breed_type (Literal["黑羽", "古早", "舍黑", "閹雞"]): 雞種類型
        status (list[Literal["all", "completed", "breeding", "sale"]]): 批次狀態
        session (Session): 數據庫會話實例
        query_service (QueryService): 查詢服務實例

    Returns:
        List[BatchAggregateResponseModel]: 特定批次名稱的批次聚合列表
    """
    try:
        filtered_aggrs = query_service.get_filtered_aggregates(
            session, batch_name=batch_name, breed_type=breed_type, status=status
        )
        logger.info(f"batch_name: {batch_name}")
        logger.info(f"breed_type: {breed_type}")
        logger.info(f"status: {status}")
        logger.info(f"filtered_aggrs: {len(filtered_aggrs)}")
        return [DTOService.batch_aggregate_to_dto(batch) for batch in filtered_aggrs]
    except Exception as e:
        logger.error(f"獲取特定批次名稱時發生錯誤: {str(e)}\n{traceback.format_exc()}")
        raise HTTPException(
            status_code=500, detail={"error": str(e), "type": type(e).__name__}
        )
