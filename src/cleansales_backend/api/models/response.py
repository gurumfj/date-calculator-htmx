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

from typing import Any, Dict, Generic, List, Optional, TypeVar

from pydantic import BaseModel, ConfigDict

# from .data_models import BatchAggregateModel

T = TypeVar("T")


class ResponseModel(BaseModel, Generic[T]):
    """通用響應模型"""

    success: bool = True
    message: str = "操作成功"
    data: Optional[T] = None
    errors: Optional[List[Dict[str, Any]]] = None

    model_config = ConfigDict(from_attributes=True)


class PaginationResponseModel(ResponseModel[List[T]], Generic[T]):
    """分頁響應模型"""

    total: int = 0
    page: int = 1
    page_size: int = 10
    total_pages: int = 0

    model_config = ConfigDict(from_attributes=True)


# class BatchAggregateResponseModel(ResponseModel):
#     """未結案入雛批次資料的回應模型

#     Attributes:
#         status (str): API 處理狀態 ('success' 或 'error')
#         msg (str): 處理結果訊息
#         content (dict): {
#             "count": 批次總數,
#             "batches": 批次資料列表
#         }
#     """

#     content: dict[str, int | list[BatchAggregateModel]] = {"count": 0, "batches": []}
