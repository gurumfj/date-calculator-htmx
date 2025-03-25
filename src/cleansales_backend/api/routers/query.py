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

import hashlib
import json
import logging
from datetime import datetime, timedelta
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response
from fastapi.responses import JSONResponse

from cleansales_backend.domain.models.batch_aggregate import (
    BatchAggregateModel,
    SaleRecordModel,
)
from cleansales_backend.domain.models.feed_record import FeedRecord
from cleansales_backend.processors import BreedRecordProcessor, SaleRecordProcessor
from cleansales_backend.processors.feeds_schema import FeedRecordProcessor
from cleansales_backend.services import QueryService

from .. import core_db
from ..models import ContextModel, ResponseModel

# 配置查詢路由器專用的日誌記錄器
logger = logging.getLogger(__name__)


# 創建路由器實例，設置前綴和標籤
router = APIRouter(prefix="/api", tags=["api"])

_breed_repository = BreedRecordProcessor()
_sale_repository = SaleRecordProcessor()
_feed_repository = FeedRecordProcessor()
_query_service = QueryService(
    _breed_repository,
    _sale_repository,
    _feed_repository,
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
    deprecated=True,
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
        all_aggregates = query_service.get_batch_aggregates()
        data = query_service.get_batch_aggregates_by_criteria(
            all_aggregates, period=(datetime.now() - timedelta(days=60), datetime.now())
        )
        return ResponseModel(
            success=True if data else False,
            message=f"獲取{len(data)}筆未結案批次" if data else "未找到未結案批次",
            content=ContextModel(
                data=[BatchAggregateModel.create_from(aggregate) for aggregate in data]
            ),
        )
    except Exception as e:
        logger.error(f"獲取未結案批次時發生錯誤: {e}")
        raise HTTPException(
            status_code=500, detail={"error": str(e), "type": type(e).__name__}
        )


@router.get(
    "/batch",
    response_model_exclude_unset=True,
    response_model_exclude_none=True,
)
async def get_batch_aggregates_by_criteria(
    query_service: Annotated[QueryService, Depends(get_query_service)],
    request: Request,
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
    start_date: datetime | None = Query(
        default=None,
        description="開始日期。空列表或 None 表示不過濾狀態",
    ),
    end_date: datetime | None = Query(
        default=None,
        description="結束日期。空列表或 None 表示不過濾狀態",
    ),
) -> Response:
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
        batch_status_set = set(batch_status) if batch_status is not None else None
        period = (start_date, end_date) if start_date and end_date else None

        all_aggregates = query_service.get_batch_aggregates()
        filtered_aggregates = query_service.get_batch_aggregates_by_criteria(
            all_aggregates, batch_name, breed_type, batch_status_set, period
        )

        result = [
            BatchAggregateModel.create_from(aggregate).model_dump(mode="json")
            for aggregate in filtered_aggregates
        ]
        # 先將結果轉換為 JSON 字符串
        content_str = json.dumps(result)
        content_bytes = content_str.encode("utf-8")

        etag = hashlib.md5(content_bytes).hexdigest()

        if request.headers.get("If-None-Match") == etag:
            response = Response(
                status_code=304,
                headers={"ETag": etag},
            )
            return response

        response = JSONResponse(
            content=result,
            status_code=200,
            headers={"ETag": etag},
        )
        return response
    except Exception as e:
        logger.error(f"獲取批次聚合時發生錯誤: {e}")
        raise HTTPException(
            status_code=500, detail={"error": str(e), "type": type(e).__name__}
        )


@router.get(
    "/sales/{batch_name}",
    response_model=list[SaleRecordModel],
    response_model_exclude_unset=True,
    response_model_exclude_none=True,
)
async def get_sales_data(
    query_service: Annotated[QueryService, Depends(get_query_service)],
    batch_name: str,
) -> Response:
    try:
        all_aggregates = query_service.get_batch_aggregates()
        filtered_aggregates = query_service.get_batch_aggregates_by_criteria(
            all_aggregates, batch_name=batch_name
        )
        sales = [
            SaleRecordModel.create_from(sale, aggregate.breeds)
            for aggregate in filtered_aggregates
            if aggregate.sales
            for sale in aggregate.sales
        ]
        return JSONResponse(
            content=[sale.model_dump(mode="json") for sale in sales],
            status_code=200,
        )
    except Exception as e:
        logger.error(f"獲取銷售資料時發生錯誤: {e}")
        raise HTTPException(
            status_code=500, detail={"error": str(e), "type": type(e).__name__}
        )


@router.get(
    "/feeds/{batch_name}",
    response_model=list[FeedRecord],
    response_model_exclude_unset=True,
    response_model_exclude_none=True,
)
async def get_feeds_data(
    query_service: Annotated[QueryService, Depends(get_query_service)],
    batch_name: str,
) -> Response:
    try:
        all_aggregates = query_service.get_batch_aggregates()
        filtered_aggregates = query_service.get_batch_aggregates_by_criteria(
            all_aggregates, batch_name=batch_name
        )
        feeds = [
            feed.model_dump(mode="json")
            for aggregate in filtered_aggregates
            if aggregate.feeds
            for feed in aggregate.feeds
        ]

        response = JSONResponse(
            content=feeds,
            status_code=200,
        )
        return response
    except Exception as e:
        logger.error(f"獲取飼料資料時發生錯誤: {e}")
        raise HTTPException(
            status_code=500, detail={"error": str(e), "type": type(e).__name__}
        )
