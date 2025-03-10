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

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session

from cleansales_refactor.domain.models import BatchAggregate, SaleRecord
from cleansales_refactor.services import QueryService

from .. import get_session
from ..models import (
    BatchAggregateResponseModel,
    SalesRecordResponseModel,
)

# 配置查詢路由器專用的日誌記錄器
logger = logging.getLogger(__name__)

# 初始化查詢服務實例
query_service = QueryService()

# 創建路由器實例，設置前綴和標籤
router = APIRouter(prefix="/api", tags=["api"])


@router.get("/not-completed", response_model=list[BatchAggregateResponseModel])
async def get_breeding_data(
    session: Session = Depends(get_session),
) -> list[BatchAggregateResponseModel]:
    """
    獲取所有未結案的入雛批次資料

    Args:
        session (Session): 數據庫會話實例

    Returns:
        list[BatchAggregateResponseModel]: 未結案批次資料列表

    Raises:
        HTTPException: 當查詢過程中出現錯誤時
    """
    try:
        # 執行查詢
        query_result = query_service.get_breeds_is_not_completed(session)
        # 轉換為 DTO 並返回
        return [DTOService.batch_aggregate_to_dto(q) for q in query_result]
    except Exception as e:
        # 詳細記錄錯誤信息
        error_msg = f"取得未結案的入雛批次資料時發生錯誤: {str(e)}\n"
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


@router.get("/q/{batch_name}", response_model=list[BatchAggregateResponseModel])
async def get_sales_by_batch_name(
    batch_name: str,
    session: Session = Depends(get_session),
) -> list[BatchAggregateResponseModel]:
    """
    根據批次名稱查詢特定批次的資料

    Args:
        batch_name (str): 要查詢的批次名稱
        session (Session): 數據庫會話實例

    Returns:
        list[BatchAggregateResponseModel]: 符合批次名稱的資料列表
    """
    # 執行查詢並轉換為 DTO
    query_result = query_service.get_breed_by_batch_name(session, batch_name)
    return [DTOService.batch_aggregate_to_dto(q) for q in query_result]


@router.get("/sales", response_model=list[SalesRecordResponseModel])
async def get_sales_data(
    limit: int = Query(default=100, ge=1, le=300),
    offset: int = Query(default=0, ge=0),
    session: Session = Depends(get_session),
) -> list[SalesRecordResponseModel]:
    """
    獲取銷售記錄數據，支持分頁

    Args:
        limit (int): 每頁記錄數量，範圍 1-300
        offset (int): 起始位置，從 0 開始
        session (Session): 數據庫會話實例

    Returns:
        list[SalesRecordResponseModel]: 銷售記錄列表

    Raises:
        HTTPException: 當查詢過程中出現錯誤時
    """
    try:
        # 執行分頁查詢
        query_result = query_service.get_sales_data(session, limit, offset)
        # 轉換為 DTO 並返回
        return [DTOService.sales_record_to_dto(sale) for sale in query_result]
    except Exception as e:
        # 詳細記錄錯誤信息
        error_msg = f"取得銷售資料時發生錯誤: {str(e)}\n"
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


class DTOService:
    """
    數據傳輸對象（DTO）服務類

    負責將域模型對象轉換為 API 響應模型，實現數據層和表現層的解耦
    """

    @staticmethod
    def batch_aggregate_to_dto(
        data_model: BatchAggregate,
    ) -> BatchAggregateResponseModel:
        """
        將批次聚合域模型轉換為 API 響應模型

        Args:
            data_model (BatchAggregate): 批次聚合域模型實例

        Returns:
            BatchAggregateResponseModel: API 響應模型實例
        """
        return BatchAggregateResponseModel(
            batch_name=data_model.batch_name,
            farm_name=data_model.farm_name,
            address=data_model.address,
            farmer_name=data_model.farmer_name,
            total_male=data_model.total_male,
            total_female=data_model.total_female,
            veterinarian=data_model.veterinarian,
            batch_state=data_model.batch_state,
            breed_date=data_model.breed_date,
            supplier=data_model.supplier,
            chicken_breed=data_model.chicken_breed,
            male=data_model.male,
            female=data_model.female,
            day_age=data_model.day_age,
            week_age=data_model.week_age,
            sales_male=data_model.sales_male,
            sales_female=data_model.sales_female,
            total_sales=data_model.total_sales,
            sales_percentage=data_model.sales_percentage,
        )

    @staticmethod
    def sales_record_to_dto(data_model: SaleRecord) -> SalesRecordResponseModel:
        """
        將銷售記錄域模型轉換為 API 響應模型

        Args:
            data_model (SaleRecord): 銷售記錄域模型實例

        Returns:
            SalesRecordResponseModel: API 響應模型實例
        """
        return SalesRecordResponseModel(
            closed=data_model.closed,
            handler=data_model.handler,
            date=data_model.date,
            location=data_model.location,
            customer=data_model.customer,
            male_count=data_model.male_count,
            female_count=data_model.female_count,
            total_weight=data_model.total_weight,
            total_price=data_model.total_price,
            male_price=data_model.male_price,
            female_price=data_model.female_price,
            unpaid=data_model.unpaid,
        )
