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
from datetime import datetime
from typing import Annotated, Any, Literal

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlmodel import Session

from cleansales_backend.api.services.dto_service import DTOService
from cleansales_backend.domain.models.batch_state import BatchState
from cleansales_backend.processors import BreedRecordProcessor, SaleRecordProcessor
from cleansales_backend.processors.interface.processors_interface import IResponse

# from cleansales_backend.repositories import BreedRepository, SaleRepository
from cleansales_backend.services import QueryService

from .. import core_db

# 配置查詢路由器專用的日誌記錄器
logger = logging.getLogger(__name__)

# 創建路由器實例，設置前綴和標籤
router = APIRouter(prefix="/api", tags=["api"])

_breed_repository = BreedRecordProcessor()
_sale_repository = SaleRecordProcessor()
_query_service = QueryService(
    _breed_repository,
    _sale_repository,
)


def get_query_service() -> QueryService:
    """依賴注入：獲取查詢服務實例

    Returns:
        QueryService: 查詢服務實例
    """
    return _query_service


class BatchStatisticsResponse(BaseModel):
    """批次統計響應模型"""

    batch_info: dict[str, Any]
    totals: dict[str, Any]
    customer_statistics: dict[str, dict[str, float]]
    sales_trends: dict[str, list[dict[str, Any]]]


@router.get("/not-completed", response_model=IResponse)
async def get_not_completed_batches(
    session: Annotated[Session, Depends(core_db.get_session)],
    query_service: Annotated[QueryService, Depends(get_query_service)],
) -> IResponse:
    """獲取未結案的批次列表

    Args:
        session (Session): 數據庫會話實例
        query_service (QueryService): 查詢服務實例

    Returns:
        IResponse: 包含未結案批次列表的響應
    """
    try:
        all_aggrs = query_service.get_batch_aggregates(session)
        filtered_aggrs = [
            aggr
            for aggr in all_aggrs
            if aggr.batch_state in [BatchState.BREEDING, BatchState.SALE]
        ]
        data = [DTOService.batch_aggregate_to_dto(batch) for batch in filtered_aggrs]
        return IResponse(
            success=True,
            message=f"獲取{len(data)}筆未結案批次",
            content={
                "timestamp": datetime.now().isoformat(),
                "data": data,
            },
        )
    except Exception as e:
        logger.error(f"獲取未結案批次時發生錯誤: {str(e)}\n{traceback.format_exc()}")
        raise HTTPException(
            status_code=500, detail={"error": str(e), "type": type(e).__name__}
        )


@router.get("/batch", response_model=IResponse)
async def get_batch_aggregates_by_criteria(
    session: Annotated[Session, Depends(core_db.get_session)],
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
) -> IResponse:
    """獲取特定批次名稱的批次聚合列表

    Args:
        batch_name (str): 批次名稱
        breed_type (Literal["黑羽", "古早", "舍黑", "閹雞"]): 雏種類型
        batch_status (list[Literal["completed", "breeding", "sale"]]): 批次狀態
        session (Session): 數據庫會話實例
        query_service (QueryService): 查詢服務實例

    Returns:
        IResponse: 包含特定批次名稱的批次聚合列表的響應
    """
    try:
        # if batch_state:=status:

        all_aggrs = query_service.get_batch_aggregates(session)
        logger.info(f"criteria: {batch_status, batch_name, breed_type}")
        filtered_aggrs = [
            aggr
            for aggr in all_aggrs
            if (
                (
                    batch_name is None
                    or aggr.batch_name is not None
                    and batch_name in aggr.batch_name
                )
                and (
                    batch_status is None
                    or aggr.batch_state in [BatchState(s) for s in batch_status]
                )
                and (
                    breed_type is None
                    or any(breed_type in breed.chicken_breed for breed in aggr.breeds)
                )
            )
        ]

        data = [DTOService.batch_aggregate_to_dto(batch) for batch in filtered_aggrs]
        return IResponse(
            success=True,
            message=f"獲取{len(filtered_aggrs)}筆批次聚合",
            content={"data": data},
        )
    except Exception as e:
        logger.error(f"獲取特定批次名稱時發生錯誤: {str(e)}\n{traceback.format_exc()}")
        raise HTTPException(
            status_code=500, detail={"error": str(e), "type": type(e).__name__}
        )
