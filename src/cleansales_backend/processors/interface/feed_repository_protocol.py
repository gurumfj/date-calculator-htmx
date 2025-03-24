from typing import Protocol, runtime_checkable

from sqlmodel import Session

from cleansales_backend.domain.models import FeedRecord


@runtime_checkable
class FeedRepositoryProtocol(Protocol):
    """飼料記錄倉儲協議

    定義了查詢服務（QueryService）所需的倉儲操作。
    主要包括：
    1. 根據批次狀態查詢
    2. 根據批次名稱查詢
    """

    def get_by_batch_name(self, session: Session, batch_name: str) -> list[FeedRecord]:
        """根據批次名稱查詢飼料記錄

        Args:
            batch_name (str): 批次名稱（支持模糊匹配）

        Returns:
            list[FeedRecord]: 符合條件的飼料記錄列表
        """
        ...
