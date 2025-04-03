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

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    Request,
    Response,
)
from fastapi.responses import JSONResponse

from cleansales_backend.api import get_query_service
from cleansales_backend.domain.models.batch_aggregate import (
    BatchAggregateModel,
    SaleRecordModel,
)
from cleansales_backend.domain.models.feed_record import FeedRecord
from cleansales_backend.services import QueryService

from ..models import ContextModel, ResponseModel

# 配置查詢路由器專用的日誌記錄器
logger = logging.getLogger(__name__)


# 創建路由器實例，設置前綴和標籤
router = APIRouter(prefix="/api", tags=["api"])


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
async def get_sales_data_url_params(
    query_service: Annotated[QueryService, Depends(get_query_service)],
    request: Request,
    batch_name: str,
) -> Response:
    return await get_sales_data(query_service, request, batch_name)


@router.get(
    "/sales",
    response_model=list[SaleRecordModel],
    response_model_exclude_unset=True,
    response_model_exclude_none=True,
)
async def get_sales_data_query(
    query_service: Annotated[QueryService, Depends(get_query_service)],
    request: Request,
    batch_name: str = Query(
        ...,
        description="批次名稱",
    ),
) -> Response:
    return await get_sales_data(query_service, request, batch_name)


async def get_sales_data(
    query_service: Annotated[QueryService, Depends(get_query_service)],
    request: Request,
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
        content_str = json.dumps([sale.model_dump(mode="json") for sale in sales])
        content_bytes = content_str.encode("utf-8")
        etag = hashlib.md5(content_bytes).hexdigest()

        if request.headers.get("If-None-Match") == etag:
            return Response(status_code=304, headers={"ETag": etag})

        return JSONResponse(
            content=[sale.model_dump(mode="json") for sale in sales],
            status_code=200,
            headers={"ETag": etag},
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
async def get_feeds_data_url_params(
    query_service: Annotated[QueryService, Depends(get_query_service)],
    request: Request,
    batch_name: str,
) -> Response:
    return await get_feeds_data(query_service, request, batch_name)


@router.get(
    "/feeds",
    response_model=list[FeedRecord],
    response_model_exclude_unset=True,
    response_model_exclude_none=True,
)
async def get_feeds_data_query(
    query_service: Annotated[QueryService, Depends(get_query_service)],
    request: Request,
    batch_name: str = Query(
        ...,
        description="批次名稱",
    ),
) -> Response:
    return await get_feeds_data(query_service, request, batch_name)


async def get_feeds_data(
    query_service: Annotated[QueryService, Depends(get_query_service)],
    request: Request,
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
        content_str = json.dumps([feed for feed in feeds])
        content_bytes = content_str.encode("utf-8")
        etag = hashlib.md5(content_bytes).hexdigest()

        if request.headers.get("If-None-Match") == etag:
            return Response(status_code=304, headers={"ETag": etag})

        response = JSONResponse(
            content=feeds,
            status_code=200,
            headers={"ETag": etag},
        )
        return response
    except Exception as e:
        logger.error(f"獲取飼料資料時發生錯誤: {e}")
        raise HTTPException(
            status_code=500, detail={"error": str(e), "type": type(e).__name__}
        )


@router.get(
    "/excel-sales",
    response_model_exclude_unset=True,
    response_model_exclude_none=True,
)
async def get_excel_sales_data(
    query_service: Annotated[QueryService, Depends(get_query_service)],
    request: Request,
    page: int = Query(default=1, ge=1, description="當前頁碼，從1開始"),
    page_size: int = Query(default=100, ge=1, le=1000, description="每頁記錄數量"),
    batch_name: str | None = Query(
        default=None,
        description="批次名稱過濾條件",
    ),
    breed_type: Literal["黑羽", "古早", "舍黑", "閹雞"] | None = Query(
        default=None,
        description="雞種類型過濾條件",
    ),
    batch_status: list[Literal["completed", "breeding", "sale"]] | None = Query(
        default=["sale"],
        description="批次狀態過濾條件，可包含多個狀態",
    ),
    start_date: datetime | None = Query(
        default=None,
        description="開始日期過濾條件",
    ),
    end_date: datetime | None = Query(
        default=None,
        description="結束日期過濾條件",
    ),
    sort_by: str | None = Query(
        default="sale_date",
        description="排序字段，例如'sale_date'、'batch_name'等",
    ),
    sort_desc: bool = Query(
        default=True,
        description="是否降序排序",
    ),
) -> Response:
    """獲取格式化的銷售數據，適合Excel或Google Apps Script使用

    此API提供分頁功能，並以扁平化格式返回銷售數據，
    方便Excel或Google Apps Script進行處理和展示。
    """
    try:
        # 處理批次狀態過濾條件
        batch_status_set = set(batch_status) if batch_status else None

        # 處理日期範圍過濾條件
        period = (start_date, end_date) if start_date and end_date else None

        # 獲取所有批次數據
        all_aggregates = query_service.get_batch_aggregates()

        # 獲取分頁的銷售數據
        sales_data, pagination = query_service.get_paginated_sales_data(
            all_aggregates=all_aggregates,
            page=page,
            page_size=page_size,
            batch_name=batch_name,
            breed_type=breed_type,
            batch_status=batch_status_set,
            period=period,
            sort_by=sort_by,
            sort_desc=sort_desc,
        )

        # 準備元數據
        meta = {
            "generated_at": datetime.now().isoformat(),
            "filters": {
                "batch_name": batch_name,
                "breed_type": breed_type,
                "batch_status": batch_status,
                "start_date": start_date.isoformat() if start_date else None,
                "end_date": end_date.isoformat() if end_date else None,
            },
            "sorting": {
                "sort_by": sort_by,
                "sort_desc": sort_desc,
            },
        }

        # 準備響應數據
        response_data = {
            "data": sales_data,
            "pagination": pagination,
            "meta": meta,
        }

        # 生成ETag
        content_str = json.dumps(response_data)
        content_bytes = content_str.encode("utf-8")
        etag = hashlib.md5(content_bytes).hexdigest()

        # 檢查是否有變更
        if request.headers.get("If-None-Match") == etag:
            return Response(status_code=304, headers={"ETag": etag})

        # 返回數據
        return JSONResponse(
            content=response_data,
            status_code=200,
            headers={"ETag": etag},
        )
    except Exception as e:
        logger.error(f"獲取Excel格式銷售數據時發生錯誤: {e}")
        import traceback

        logger.error(traceback.format_exc())
        raise HTTPException(
            status_code=500, detail={"error": str(e), "type": type(e).__name__}
        )


__all__ = [
    "router",
    "get_batch_aggregates_by_criteria",
    "get_sales_data",
    "get_feeds_data",
    "get_query_service",
]
