"""
################################################################################
# API 響應模型模組
#
# 這個模組提供了 API 響應的通用模型，包括：
# - 成功響應
# - 錯誤響應
# - 分頁響應
#
# 主要功能：
# - 統一響應格式
# - 錯誤處理
# - 分頁支持
################################################################################
"""

from datetime import datetime
from typing import Any, Generic, TypeVar

from pydantic import BaseModel, ConfigDict
from typing_extensions import deprecated

# from .data_models import BatchAggregateModel

T = TypeVar("T")
D = TypeVar("D", bound=BaseModel)


@deprecated("No longer used")
class ContextModel(BaseModel, Generic[D]):
    """包含資料列表的上下文模型"""

    data: list[D]

    model_config = ConfigDict(
        arbitrary_types_allowed=True, json_schema_extra={"example": {"data": []}}
    )


@deprecated("No longer used")
class ResponseModel(BaseModel, Generic[D]):
    """標準響應模型

    包含成功狀態、訊息和資料內容
    """

    success: bool = True
    message: str = "操作成功"
    last_updated_at: datetime | None = None
    content: ContextModel[D]
    errors: list[dict[str, Any]] | None = None
    model_config = ConfigDict(from_attributes=True)


class PaginationResponseModel(ResponseModel[ContextModel[D]], Generic[D]):
    """分頁響應模型"""

    total: int = 0
    page: int = 1
    page_size: int = 10
    total_pages: int = 0

    model_config = ConfigDict(from_attributes=True)
