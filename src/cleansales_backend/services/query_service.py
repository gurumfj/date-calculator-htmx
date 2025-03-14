import logging
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Literal

from sqlmodel import Session

from cleansales_backend.domain.models import (
    BatchAggregate,
    BatchState,
    BreedRecord,
    SaleRecord,
)

# from cleansales_backend.domain.models.batch_aggregate import BatchAggregate
from cleansales_backend.repositories import (
    BreedRepositoryProtocol,
    SaleRepositoryProtocol,
)

logger = logging.getLogger(__name__)


@dataclass
class BatchFilterCriteria:
    """批次過濾準則

    封裝批次過濾的業務規則參數

    Attributes:
        batch_name: 批次名稱關鍵字
        breed_type: 品種類型關鍵字
        status: 批次狀態列表，可包含多個狀態。空列表或 ["all"] 表示不過濾狀態
    """

    batch_name: str | None = None
    breed_type: str | None = None
    status: list[Literal["all", "completed", "breeding", "sale"]] = field(
        default_factory=lambda: ["all"]
    )


class BatchFilterService:
    """批次過濾服務

    提供純函數方式的批次資料過濾功能
    不包含任何副作用，專注於過濾邏輯的處理
    """

    @staticmethod
    def filter_batches(
        aggregates: list[BatchAggregate], criteria: BatchFilterCriteria
    ) -> list[BatchAggregate]:
        """根據過濾準則過濾批次資料

        純函數：根據給定的準則過濾批次聚合資料

        Args:
            aggregates: 原始批次聚合資料
            criteria: 過濾準則

        Returns:
            符合準則的批次聚合資料列表
        """
        result: list[BatchAggregate] = aggregates

        if criteria.batch_name:
            result = [
                aggr
                for aggr in result
                if aggr.batch_name and criteria.batch_name in aggr.batch_name
            ]

        if criteria.breed_type:
            result = [
                aggr
                for aggr in result
                if aggr.chicken_breed
                and criteria.breed_type
                in [breed.chicken_breed for breed in aggr.breeds]
            ]

        # 如果狀態列表為空或包含 "all"，則不進行狀態過濾
        if criteria.status and "all" not in criteria.status:
            state_map = {
                "completed": BatchState.COMPLETED,
                "breeding": BatchState.BREEDING,
                "sale": BatchState.SALE,
            }
            # 將文字狀態轉換為 BatchState 列舉值
            states = [state_map[s] for s in criteria.status if s in state_map]
            # 過濾出符合任一指定狀態的批次
            result = [aggr for aggr in result if aggr.batch_state in states]

        return result


class QueryService:
    """查詢服務

    負責數據查詢和聚合的協調工作：
    1. 通過 repositories 獲取數據（side effect）
    2. 創建 BatchAggregate 實例
    3. 協調過濾服務進行資料過濾
    """

    _breed_repository: BreedRepositoryProtocol
    _sale_repository: SaleRepositoryProtocol
    _filter_service: BatchFilterService

    def __init__(
        self,
        breed_repository: BreedRepositoryProtocol,
        sale_repository: SaleRepositoryProtocol,
        filter_service: BatchFilterService | None = None,
    ) -> None:
        self._breed_repository = breed_repository
        self._sale_repository = sale_repository
        self._filter_service = filter_service or BatchFilterService()

    def get_batch_aggregates(self, session: Session) -> list[BatchAggregate]:
        """獲取所有批次聚合

        將養殖記錄按批次分組並聚合相關銷售記錄

        Args:
            session (Session): 數據庫會話

        Returns:
            list[BatchAggregate]: 批次聚合列表，包含每個批次的養殖和銷售記錄
        """
        try:
            # 使用海象運算符簡化代碼流程
            if not (breeds := self._breed_repository.get_all(session)):
                return []

            # 使用 defaultdict 進行分組
            breed_groups: dict[str, list[BreedRecord]] = defaultdict(list)
            for breed in breeds:
                if breed.batch_name:  # 確保 batch_name 不為 None
                    breed_groups[breed.batch_name].append(breed)

            # 創建並返回批次聚合列表
            return [
                BatchAggregate(
                    breeds=breeds,
                    sales=self._sale_repository.get_sales_by_location(
                        session, batch_name
                    ),
                )
                for batch_name, breeds in breed_groups.items()
            ]
        except Exception as e:
            logger.error(f"獲取批次聚合數據時發生錯誤: {e}")
            raise ValueError(f"獲取批次聚合數據時發生錯誤: {str(e)}")

    def get_filtered_aggregates(
        self,
        session: Session,
        batch_name: str | None = None,
        breed_type: str | None = None,
        status: list[Literal["all", "completed", "breeding", "sale"]] | None = None,
        batch_state: BatchState | None = None,
    ) -> list[BatchAggregate]:
        """獲取已過濾的批次聚合資料

        Args:
            session: 數據庫會話
            batch_name: 批次名稱關鍵字
            breed_type: 品種類型關鍵字
            status: 批次狀態列表，None 或 ["all"] 表示不過濾狀態
            batch_state: 批次狀態，None 表示不過濾狀態
        """
        try:
            aggregates = self.get_batch_aggregates(session)
            criteria = BatchFilterCriteria(
                batch_name=batch_name, breed_type=breed_type, status=status or ["all"]
            )
            return self._filter_service.filter_batches(aggregates, criteria)
        except Exception as e:
            logger.error(f"過濾批次聚合資料時發生錯誤: {e}")
            raise ValueError(f"資料過濾失敗: {str(e)}")

    def get_sales_data(
        self, session: Session, limit: int = 30, offset: int = 0
    ) -> list[SaleRecord]:
        """獲取銷售記錄

        Args:
            session: 數據庫會話
            limit: 限制返回的記錄數量
            offset: 偏移量

        Returns:
            list[SaleRecord]: 銷售記錄列表
        """
        return self._sale_repository.get_sales_data(session, limit, offset)
