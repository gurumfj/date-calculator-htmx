# """
# ################################################################################
# # 養殖記錄倉儲模組
# #
# # 這個模組提供了養殖記錄的數據訪問層，包括：
# # 1. 基本的 CRUD 操作
# # 2. 批次相關查詢
# # 3. 統計數據查詢
# #
# # 主要功能：
# # - 養殖記錄的增刪改查
# # - 批次相關的數據查詢
# # - 養殖統計數據獲取
# ################################################################################
# """

from typing import Protocol, runtime_checkable

from sqlmodel import Session

from cleansales_backend.domain.models import BreedRecord


@runtime_checkable
class BreedRepositoryProtocol(Protocol):
    """養殖記錄倉儲協議

    定義了查詢服務（QueryService）所需的倉儲操作。
    主要包括：
    1. 根據批次狀態查詢
    2. 根據批次名稱查詢
    """

    def get_all(self, session: Session) -> list[BreedRecord]:
        """獲取所有養殖記錄

        Args:
            session (Session): 數據庫會話

        Returns:
            list[BreedRecord]: 所有養殖記錄列表
        """
        ...

    def get_by_batch_name(self, session: Session, batch_name: str) -> list[BreedRecord]:
        """根據批次名稱查詢養殖記錄

        Args:
            batch_name (str): 批次名稱（支持模糊匹配）

        Returns:
            list[BreedRecord]: 符合條件的養殖記錄列表
        """
        ...
