import logging
from collections import defaultdict

from sqlmodel import Session

from cleansales_refactor.domain.models import (
    BatchAggregate,
    BreedRecord,
)
from cleansales_refactor.repositories import (
    BreedRepositoryProtocol,
    SaleRepositoryProtocol,
)

logger = logging.getLogger(__name__)


class QueryService:
    """查詢服務

    負責創建 BatchAggregate 實例。主要功能：
    1. 通過 repositories 獲取數據
    2. 創建 BatchAggregate 實例
    """

    def __init__(
        self,
        breed_repository: BreedRepositoryProtocol,
        sale_repository: SaleRepositoryProtocol,
    ):
        self.breed_repository = breed_repository
        self.sale_repository = sale_repository

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
            if not (breeds := self.breed_repository.get_all(session)):
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
                    sales=self.sale_repository.get_sales_by_location(
                        session, batch_name
                    ),
                )
                for batch_name, breeds in breed_groups.items()
            ]
        except Exception as e:
            logger.error(f"獲取批次聚合數據時發生錯誤: {e}")
            raise ValueError(f"獲取批次聚合數據時發生錯誤: {str(e)}")

    # def get_sales_data(self, limit: int = 300, offset: int = 0) -> list[SaleRecord]:
    #     """獲取銷售記錄數據
    #     TODO: 需要建構獲取 raw sales data 的 presentation layer
    #     Args:
    #         limit (int, optional): 返回記錄的最大數量. Defaults to 300.
    #         offset (int, optional): 起始位置. Defaults to 0.

    #     Returns:
    #         List[SaleRecord]: 銷售記錄列表
    #     """
    #     return self.sale_repository.get_sales_data(limit=limit, offset=offset)
