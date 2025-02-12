from typing import Any

from sqlmodel import SQLModel

from ..models.breed import BatchAggregateModel


class ResponseModel(SQLModel):
    status: str
    msg: str
    content: dict[str, Any]


class BatchAggregateResponseModel(ResponseModel):
    """未結案入雛批次資料的回應模型

    Attributes:
        status (str): API 處理狀態 ('success' 或 'error')
        msg (str): 處理結果訊息
        content (dict): {
            "count": 批次總數,
            "batches": 批次資料列表
        }
    """

    content: dict[str, int | list[BatchAggregateModel]] = {"count": 0, "batches": []}
