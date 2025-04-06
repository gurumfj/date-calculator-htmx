"""
################################################################################
# 原始數據查詢路由模組
#
# 這個模組提供了所有與原始數據查詢相關的 API 端點，包括：
# - 批次原始數據查詢
# - 帶篩選條件的批次原始數據查詢
#
# 主要功能：
# 1. 提供未經業務邏輯處理的原始數據
# 2. 支持選擇性包含breeds/sales/feeds數據
# 3. 支持與標準API相同的篩選條件
################################################################################
"""

import hashlib
import json
import logging
from datetime import datetime
from typing import Annotated, Literal

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Path,
    Query,
    Request,
    Response,
)
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from cleansales_backend.domain.models.batch_aggregate import BatchRecordModel
from cleansales_backend.domain.models.batch_state import BatchState
from cleansales_backend.domain.models.feed_record import FeedRecord
from cleansales_backend.domain.models.sale_record import SaleRecord
from cleansales_backend.processors.interface.breed_repository_protocol import (
    BreedRepositoryCriteria,
)
from cleansales_backend.services import QueryService

from .. import get_query_service

# 配置查詢路由器專用的日誌記錄器
logger = logging.getLogger(__name__)

# 創建路由器實例，設置前綴和標籤
router = APIRouter(prefix="/api/raw", tags=["raw"])


class RawBatchDataResponse(BaseModel):
    batch_name: str | None
    farm_name: str
    address: str | None
    farmer_name: str | None
    veterinarian: str | None
    batch_state: BatchState
    breeds: list[BatchRecordModel]
    sales: list[SaleRecord]
    feeds: list[FeedRecord]


@router.get(
    "/batch",
    response_model=RawBatchDataResponse,
    response_model_exclude_unset=True,
    response_model_exclude_none=True,
)
async def get_raw_batch_data(
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
    include_breeds: bool = Query(default=True, description="是否包含入雛記錄"),
    include_sales: bool = Query(default=True, description="是否包含銷售記錄"),
    include_feeds: bool = Query(default=True, description="是否包含飼料記錄"),
) -> Response:
    """獲取原始的批次資料，支持選擇性包含不同類型的記錄

    此API端點返回未經過業務邏輯處理的原始批次數據，
    讓前端可以根據需要自行計算和處理數據。

    Args:
        batch_name (str): 批次名稱篩選條件
        breed_type (str): 雞種篩選條件
        batch_status (list): 批次狀態篩選條件
        start_date/end_date (datetime): 日期範圍篩選條件
        include_breeds/include_sales/include_feeds (bool): 是否包含各類記錄

    Returns:
        Response: 包含原始批次數據的JSON響應
    """
    try:
        criteria = BreedRepositoryCriteria(
            batch_name=batch_name,
            chicken_breed=breed_type,
            is_completed=None
            if batch_status is None
            else True
            if "completed" in batch_status
            else False,
            period=(
                start_date.replace(hour=0, minute=0, second=0, microsecond=0),
                end_date.replace(hour=0, minute=0, second=0, microsecond=0),
            )
            if start_date and end_date
            else None,
        )

        filtered_aggregates = query_service.get_batch_aggregates_by_repository(criteria)

        # 根據參數選擇性返回數據
        result = [
            RawBatchDataResponse(
                batch_name=aggregate.batch_name,
                farm_name=aggregate.farm_name,
                address=aggregate.address,
                farmer_name=aggregate.farmer_name,
                veterinarian=aggregate.veterinarian,
                batch_state=aggregate.batch_state,
                breeds=aggregate.batch_records if include_breeds else [],
                sales=aggregate.sales if include_sales else [],
                feeds=aggregate.feeds if include_feeds else [],
            ).model_dump(mode="json")
            for aggregate in filtered_aggregates
        ]

        # 生成 ETag 並處理 304 響應
        content_str = json.dumps(result)
        content_bytes = content_str.encode("utf-8")
        etag = hashlib.md5(content_bytes).hexdigest()

        if request.headers.get("If-None-Match") == etag:
            return Response(
                status_code=304,
                headers={"ETag": etag},
            )

        return JSONResponse(
            content=result,
            status_code=200,
            headers={"ETag": etag},
        )
    except Exception as e:
        logger.error(f"獲取原始批次數據時發生錯誤: {e}")
        raise HTTPException(
            status_code=500, detail={"error": str(e), "type": type(e).__name__}
        )


@router.get(
    "/batch/{batch_name}",
    response_model_exclude_unset=True,
    response_model_exclude_none=True,
)
async def get_raw_batch_data_by_name(
    query_service: Annotated[QueryService, Depends(get_query_service)],
    request: Request,
    batch_name: str = Path(..., description="批次名稱"),
    include_breeds: bool = Query(default=True, description="是否包含入雛記錄"),
    include_sales: bool = Query(default=True, description="是否包含銷售記錄"),
    include_feeds: bool = Query(default=True, description="是否包含飼料記錄"),
) -> Response:
    """獲取指定批次名稱的原始數據

    此API端點返回特定批次的未經過業務邏輯處理的原始數據，
    讓前端可以根據需要自行計算和處理數據。

    Args:
        batch_name (str): 指定的批次名稱
        include_breeds/include_sales/include_feeds (bool): 是否包含各類記錄

    Returns:
        Response: 包含原始批次數據的JSON響應
    """
    try:
        all_aggregates = query_service.get_batch_aggregates()
        filtered_aggregates = query_service.get_batch_aggregates_by_criteria(
            all_aggregates, batch_name=batch_name
        )

        if not filtered_aggregates:
            return JSONResponse(
                content={"detail": f"找不到批次: {batch_name}"}, status_code=404
            )

        # 只處理第一個匹配的批次
        aggregate = filtered_aggregates[0]

        batch_data = RawBatchDataResponse(
            batch_name=aggregate.batch_name,
            farm_name=aggregate.farm_name,
            address=aggregate.address,
            farmer_name=aggregate.farmer_name,
            veterinarian=aggregate.veterinarian,
            batch_state=aggregate.batch_state,
            breeds=aggregate.batch_records if include_breeds else [],
            sales=aggregate.sales if include_sales else [],
            feeds=aggregate.feeds if include_feeds else [],
        ).model_dump(mode="json")

        # 生成 ETag 並處理 304 韉應
        content_str = json.dumps(batch_data)
        content_bytes = content_str.encode("utf-8")
        etag = hashlib.md5(content_bytes).hexdigest()

        if request.headers.get("If-None-Match") == etag:
            return Response(
                status_code=304,
                headers={"ETag": etag},
            )

        return JSONResponse(
            content=batch_data,
            status_code=200,
            headers={"ETag": etag},
        )
    except Exception as e:
        logger.error(f"獲取批次 {batch_name} 的原始數據時發生錯誤: {e}")
        raise HTTPException(
            status_code=500, detail={"error": str(e), "type": type(e).__name__}
        )
