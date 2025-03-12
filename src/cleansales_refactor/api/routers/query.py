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
from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException
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


# @router.get("/q/{batch_name}", response_model=List[BatchAggregateResponseModel])
# async def get_batches_by_name(
#     batch_name: str,
#     state: Optional[str] = None,
#     query_service: QueryService = Depends(get_query_service),
# ) -> List[BatchAggregateResponseModel]:
#     """根據批次名稱和狀態查詢批次

#     Args:
#         batch_name (str): 批次名稱
#         state (Optional[str]): 批次狀態
#         query_service (QueryService): 查詢服務實例

#     Returns:
#         List[BatchAggregateResponseModel]: 符合條件的批次列表
#     """
#     try:
#         batch_state = BatchState(state) if state else None
#         batches = query_service.get_batch_aggregates_by_name_and_state(
#             batch_name, batch_state
#         )
#         return [DTOService.batch_aggregate_to_dto(batch) for batch in batches]
#     except ValueError as e:
#         logger.error(f"查詢批次時發生錯誤: {str(e)}")
#         raise HTTPException(
#             status_code=400, detail={"error": str(e), "type": type(e).__name__}
#         )
#     except Exception as e:
#         logger.error(f"查詢批次時發生錯誤: {str(e)}\n{traceback.format_exc()}")
#         raise HTTPException(
#             status_code=500, detail={"error": str(e), "type": type(e).__name__}
#         )


# @router.get("/q/state/{state}", response_model=List[BatchAggregateResponseModel])
# async def get_batches_by_state(
#     state: str,
#     query_service: QueryService = Depends(get_query_service),
# ) -> List[BatchAggregateResponseModel]:
#     """根據狀態查詢批次

#     Args:
#         state (str): 批次狀態
#         query_service (QueryService): 查詢服務實例

#     Returns:
#         List[BatchAggregateResponseModel]: 符合狀態的批次列表
#     """
#     try:
#         batch_state = BatchState(state)
#         batches = query_service.get_batch_aggregates_by_state(batch_state)
#         return [DTOService.batch_aggregate_to_dto(batch) for batch in batches]
#     except ValueError as e:
#         logger.error(f"查詢批次時發生錯誤: {str(e)}")
#         raise HTTPException(
#             status_code=400, detail={"error": str(e), "type": type(e).__name__}
#         )
#     except Exception as e:
#         logger.error(f"查詢批次時發生錯誤: {str(e)}\n{traceback.format_exc()}")
#         raise HTTPException(
#             status_code=500, detail={"error": str(e), "type": type(e).__name__}
#         )


# @router.get("/sales", response_model=list[SalesRecordResponseModel])
# async def get_sales_data(
#     limit: int = Query(default=100, ge=1, le=300),
#     offset: int = Query(default=0, ge=0),
#     query_service: QueryService = Depends(get_query_service),
# ) -> list[SalesRecordResponseModel]:
#     """
#     獲取銷售記錄數據，支持分頁

#     Args:
#         limit (int): 每頁記錄數量，範圍 1-300
#         offset (int): 起始位置，從 0 開始
#         query_service (QueryService): 查詢服務實例

#     Returns:
#         list[SalesRecordResponseModel]: 銷售記錄列表

#     Raises:
#         HTTPException: 當查詢過程中出現錯誤時
#     """
#     try:
#         # 執行分頁查詢
#         query_result = query_service.get_sales_data(limit, offset)
#         # 轉換為 DTO 並返回
#         return [DTOService.sales_record_to_dto(sale) for sale in query_result]
#     except Exception as e:
#         # 詳細記錄錯誤信息
#         error_msg = f"取得銷售資料時發生錯誤: {str(e)}\n"
#         error_msg += f"錯誤類型: {type(e).__name__}\n"
#         error_msg += f"堆疊追蹤:\n{traceback.format_exc()}"
#         logger.error(error_msg)
#         raise HTTPException(
#             status_code=500,
#             detail={
#                 "error": str(e),
#                 "type": type(e).__name__,
#                 "traceback": traceback.format_exc(),
#             },
#         )


# @router.get("/sales/statistics", response_model=SalesStatisticsResponseModel)
# async def get_sales_statistics(
#     start_date: Optional[datetime] = Query(None, description="開始日期 (YYYY-MM-DD)"),
#     end_date: Optional[datetime] = Query(None, description="結束日期 (YYYY-MM-DD)"),
#     location: Optional[str] = Query(None, description="場別"),
#     query_service: QueryService = Depends(get_query_service),
# ) -> SalesStatisticsResponseModel:
#     """
#     獲取銷售統計數據

#     Args:
#         start_date (Optional[datetime]): 開始日期
#         end_date (Optional[datetime]): 結束日期
#         location (Optional[str]): 場別
#         query_service (QueryService): 查詢服務實例

#     Returns:
#         SalesStatisticsResponseModel: 銷售統計數據
#     """
#     try:
#         statistics = query_service.get_sales_statistics(
#             start_date=start_date, end_date=end_date, location=location
#         )
#         return SalesStatisticsResponseModel(**statistics)
#     except Exception as e:
#         logger.error(f"獲取銷售統計數據時發生錯誤: {str(e)}\n{traceback.format_exc()}")
#         raise HTTPException(
#             status_code=500, detail={"error": str(e), "type": type(e).__name__}
#         )


# @router.get("/sales/trends", response_model=SalesTrendResponseModel)
# async def get_sales_trends(
#     days: int = Query(default=30, ge=1, le=365, description="要分析的天數"),
#     query_service: QueryService = Depends(get_query_service),
# ) -> SalesTrendResponseModel:
#     """
#     獲取銷售趨勢數據

#     Args:
#         days (int): 要分析的天數（1-365天）
#         query_service (QueryService): 查詢服務實例

#     Returns:
#         SalesTrendResponseModel: 銷售趨勢數據
#     """
#     try:
#         trends = query_service.get_sales_trends(days)
#         return SalesTrendResponseModel(**trends)
#     except Exception as e:
#         logger.error(f"獲取銷售趨勢數據時發生錯誤: {str(e)}\n{traceback.format_exc()}")
#         raise HTTPException(
#             status_code=500, detail={"error": str(e), "type": type(e).__name__}
#         )


# @router.get("/sales/unpaid", response_model=List[SalesRecordResponseModel])
# async def get_unpaid_sales(
#     query_service: QueryService = Depends(get_query_service),
# ) -> List[SalesRecordResponseModel]:
#     """獲取未付款的銷售記錄

#     Args:
#         query_service (QueryService): 查詢服務實例

#     Returns:
#         List[SalesRecordResponseModel]: 未付款的銷售記錄列表
#     """
#     try:
#         sales = query_service.get_unpaid_sales()
#         return [DTOService.sales_record_to_dto(sale) for sale in sales]
#     except Exception as e:
#         logger.error(
#             f"獲取未付款銷售記錄時發生錯誤: {str(e)}\n{traceback.format_exc()}"
#         )
#         raise HTTPException(
#             status_code=500, detail={"error": str(e), "type": type(e).__name__}
#         )


# @router.get(
#     "/sales/batch/{batch_name}/statistics", response_model=BatchStatisticsResponse
# )
# async def get_batch_sales_statistics(
#     batch_name: str,
#     query_service: QueryService = Depends(get_query_service),
# ) -> BatchStatisticsResponse:
#     """獲取批次銷售統計數據

#     Args:
#         batch_name (str): 批次名稱
#         query_service (QueryService): 查詢服務實例

#     Returns:
#         BatchStatisticsResponse: 批次銷售統計數據
#     """
#     try:
#         statistics = query_service.calculate_batch_sales_statistics(batch_name)
#         return BatchStatisticsResponse(**statistics)
#     except ValueError as e:
#         logger.error(f"獲取批次銷售統計數據時發生錯誤: {str(e)}")
#         raise HTTPException(
#             status_code=400, detail={"error": str(e), "type": type(e).__name__}
#         )
#     except Exception as e:
#         logger.error(
#             f"獲取批次銷售統計數據時發生錯誤: {str(e)}\n{traceback.format_exc()}"
#         )
#         raise HTTPException(
#             status_code=500, detail={"error": str(e), "type": type(e).__name__}
#         )
