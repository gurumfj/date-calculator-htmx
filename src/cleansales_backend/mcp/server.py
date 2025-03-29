"""
################################################################################
# MCP 服務器模組
#
# 這個模組提供了 MCP 服務器的實現，包括：
# 1. 工具函數註冊
# 2. 資源端點註冊
# 3. 批次數據查詢和過濾
#
# 主要功能：
# - 獲取當前日期和時間
# - 查詢未結案批次
# - 按條件查詢批次
################################################################################
"""

from datetime import datetime
from typing import Literal, Optional, List

import requests
from mcp.server.fastmcp import FastMCP

from cleansales_backend import Database, settings
from cleansales_backend.processors import (
    BreedRecordProcessor,
    FeedRecordProcessor,
    SaleRecordProcessor,
)
from cleansales_backend.processors.interface.processors_interface import IResponse
from cleansales_backend.services import QueryService
from cleansales_backend.mcp.batch_tools import (
    get_batches,
    get_batch_by_name,
    get_batches_by_breed,
    get_batches_by_status,
    get_batches_by_date_range,
)

mcp = FastMCP("cleansales-server")

db = Database(settings.DB_PATH)
sale_repository = SaleRecordProcessor()
breed_repository = BreedRecordProcessor()
feed_repository = FeedRecordProcessor()
query_service = QueryService(
    db=db,
    breed_repository=breed_repository,
    sale_repository=sale_repository,
    feed_repository=feed_repository,
)


@mcp.tool(name="today", description="Get the current date in YYYY-MM-DD format")
def get_today() -> str:
    return datetime.now().strftime("%Y-%m-%d")


@mcp.tool(name="get_current_time", description="Get the current time")
def get_current_time() -> datetime:
    """獲取當前時間

    這個函數用於方便測試時 mock 當前時間
    """
    return datetime.now()


@mcp.resource(
    uri="batch://not-completed",
    name="get_not_completed_batches",
    description="獲取銷售資料庫裡尚未結案的農場列表",
    mime_type="application/json",
)
def get_not_completed_batches() -> IResponse:
    # 發起請求
    data = requests.get("http://localhost:8888/api/not-completed").json()

    if not data:
        return IResponse(success=False, message="未找到未結案批次")

    return IResponse(
        success=True,
        message=f"獲取{len(data)}筆未結案批次",
        content={
            "data": data,
        },
    )


@mcp.tool(
    name="get_batches", 
    description="獲取批次數據，支持多種過濾條件"
)
def get_batches_tool(
    batch_name: Optional[str] = None,
    breed_type: Optional[str] = None,
    batch_status: Optional[List[str]] = None,
) -> IResponse:
    """獲取批次數據工具
    
    Args:
        batch_name: 批次名稱，如果為 None 則不過濾
        breed_type: 雞種類型 (黑羽, 古早, 舍黑, 閹雞)，如果為 None 則不過濾
        batch_status: 批次狀態列表 (completed, breeding, sale)，如果為 None 則不過濾
    
    Returns:
        IResponse: 包含批次數據的標準響應對象
    """
    # 驗證 breed_type
    valid_breed_types = ["黑羽", "古早", "舍黑", "閹雞"]
    if breed_type and breed_type not in valid_breed_types:
        return IResponse(
            success=False,
            message=f"無效的雞種類型: {breed_type}，有效值為: {', '.join(valid_breed_types)}",
            content={"error": "INVALID_BREED_TYPE"},
        )
    
    # 驗證 batch_status
    valid_statuses = ["completed", "breeding", "sale"]
    if batch_status:
        for status in batch_status:
            if status not in valid_statuses:
                return IResponse(
                    success=False,
                    message=f"無效的批次狀態: {status}，有效值為: {', '.join(valid_statuses)}",
                    content={"error": "INVALID_BATCH_STATUS"},
                )
    
    # 調用批次工具獲取數據
    return get_batches(
        batch_name=batch_name,
        breed_type=breed_type,
        batch_status=batch_status,
    )


@mcp.tool(
    name="get_batch_by_name", 
    description="根據批次名稱獲取批次數據"
)
def get_batch_by_name_tool(batch_name: str) -> IResponse:
    """根據批次名稱獲取批次數據工具
    
    Args:
        batch_name: 批次名稱
    
    Returns:
        IResponse: 包含批次數據的標準響應對象
    """
    return get_batch_by_name(batch_name=batch_name)


@mcp.tool(
    name="get_batches_by_breed", 
    description="根據雞種類型獲取批次數據"
)
def get_batches_by_breed_tool(breed_type: str) -> IResponse:
    """根據雞種類型獲取批次數據工具
    
    Args:
        breed_type: 雞種類型 (黑羽, 古早, 舍黑, 閹雞)
    
    Returns:
        IResponse: 包含批次數據的標準響應對象
    """
    # 驗證 breed_type
    valid_breed_types = ["黑羽", "古早", "舍黑", "閹雞"]
    if breed_type not in valid_breed_types:
        return IResponse(
            success=False,
            message=f"無效的雞種類型: {breed_type}，有效值為: {', '.join(valid_breed_types)}",
            content={"error": "INVALID_BREED_TYPE"},
        )
    
    return get_batches_by_breed(breed_type=breed_type)


@mcp.tool(
    name="get_batches_by_status", 
    description="根據批次狀態獲取批次數據"
)
def get_batches_by_status_tool(batch_status: List[str]) -> IResponse:
    """根據批次狀態獲取批次數據工具
    
    Args:
        batch_status: 批次狀態列表 (completed, breeding, sale)
    
    Returns:
        IResponse: 包含批次數據的標準響應對象
    """
    # 驗證 batch_status
    valid_statuses = ["completed", "breeding", "sale"]
    for status in batch_status:
        if status not in valid_statuses:
            return IResponse(
                success=False,
                message=f"無效的批次狀態: {status}，有效值為: {', '.join(valid_statuses)}",
                content={"error": "INVALID_BATCH_STATUS"},
            )
    
    return get_batches_by_status(batch_status=batch_status)


# @mcp.prompt()
# def sales_manager() -> list[Message]:
#     return [
#         UserMessage(
#             "用 get_recently_active_location 工具取得最近 5 天的銷售資料並分析。"
#         ),
#         AssistantMessage("你是專業的銷售管理員，專長是將銷售資料做分析。"),
#     ]


if __name__ == "__main__":
    mcp.run()
