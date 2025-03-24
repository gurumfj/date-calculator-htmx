"""
TODO: query location sales data from the database
"""

from datetime import datetime

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
    # aggrs = query_service.get_batch_aggregates()
    # data = query_service.get_not_completed_batches_summary(aggrs)
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
