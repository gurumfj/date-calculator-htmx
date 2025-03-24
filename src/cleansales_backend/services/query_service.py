import logging
from collections import defaultdict
from datetime import datetime
from functools import lru_cache
from typing import Literal

from sqlmodel import Session
from typing_extensions import Any

from cleansales_backend.core.database import Database
from cleansales_backend.domain.models import (
    BatchAggregate,
    BreedRecord,
)
from cleansales_backend.domain.models.batch_state import BatchState
from cleansales_backend.processors import (
    BreedRepositoryProtocol,
    FeedRepositoryProtocol,
    SaleRepositoryProtocol,
)

logger = logging.getLogger(__name__)


class QueryService:
    """查詢服務

    負責數據查詢和聚合的協調工作：
    1. 通過 repositories 獲取數據（side effect）
    2. 創建 BatchAggregate 實例
    3. 協調過濾服務進行資料過濾
    """

    _breed_repository: BreedRepositoryProtocol
    _sale_repository: SaleRepositoryProtocol
    _feed_repository: FeedRepositoryProtocol
    _db_hint: dict[str, str]
    _db: Database

    def __init__(
        self,
        breed_repository: BreedRepositoryProtocol,
        sale_repository: SaleRepositoryProtocol,
        feed_repository: FeedRepositoryProtocol,
        db: Database,
    ) -> None:
        self._breed_repository = breed_repository
        self._sale_repository = sale_repository
        self._feed_repository = feed_repository
        self._db = db
        self._db_hint = {datetime.now().isoformat(): "Started"}

    def get_batch_cache_info(self) -> dict[str, Any]:
        cache_info = {
            "get_batch_aggregates_cache_info": self.get_batch_aggregates.cache_info()._asdict(),
            "db session hint": self._db_hint,
        }
        return cache_info

    def cache_clear(self) -> None:
        logger.info("Clearing cache")
        self.get_batch_aggregates.cache_clear()
        self._db_hint = {**self._db_hint, datetime.now().isoformat(): "cache cleared"}

    @lru_cache
    def get_batch_aggregates(self) -> list[BatchAggregate]:
        with self._db.with_session() as session:
            all_aggrs, self._db_hint = self._get_batch_aggregates(
                session, self._db_hint
            )
            return all_aggrs

    def _get_batch_aggregates(
        self, session: Session, hint: dict[str, str]
    ) -> tuple[list[BatchAggregate], dict[str, str]]:
        """獲取所有批次聚合

        將養殖記錄按批次分組並聚合相關銷售記錄

        Args:
            session (Session): 數據庫會話

        Returns:
            list[BatchAggregate]: 批次聚合列表，包含每個批次的養殖和銷售記錄
        """
        try:
            # 使用 defaultdict 進行分組
            breed_groups: dict[str, list[BreedRecord]] = defaultdict(list)
            for breed in self._breed_repository.get_all(session):
                if breed.batch_name:  # 確保 batch_name 不為 None
                    breed_groups[breed.batch_name].append(breed)

            # 創建並返回批次聚合列表
            aggrs = [
                BatchAggregate(
                    breeds=breeds,
                    sales=self._sale_repository.get_sales_by_location(
                        session, batch_name
                    ),
                    feeds=self._feed_repository.get_by_batch_name(session, batch_name),
                )
                for batch_name, breeds in breed_groups.items()
            ]
            logger.info("使用資料庫獲取批次聚合數據")
            return aggrs, {**hint, datetime.now().isoformat(): "getted from database"}
        except Exception as e:
            logger.error(f"獲取批次聚合數據時發生錯誤: {e}")
            raise ValueError(f"獲取批次聚合數據時發生錯誤: {str(e)}")

    def get_batch_aggregates_by_criteria(
        self,
        all_aggrs: list[BatchAggregate],
        batch_name: str | None = None,
        breed_type: Literal["黑羽", "古早", "舍黑", "閹雞"] | None = None,
        batch_status: set[
            Literal[
                "completed",
                "breeding",
                "sale",
            ]
        ]
        | None = None,
        period: tuple[datetime, datetime] | None = None,
    ) -> list[BatchAggregate]:
        """獲取特定批次名稱的批次聚合列表

        Args:
            batch_name (str): 批次名稱
            breed_type (Literal["黑羽", "古早", "舍黑", "閹雞"]): 雏種類型
            batch_status (set[Literal["completed", "breeding", "sale"]]): 批次狀態

        Returns:
            list[BatchAggregate]: 包含特定批次名稱的批次聚合列表
        """
        logger.info(f"criteria: {batch_status, batch_name, breed_type, period}")
        return [
            aggr
            for aggr in all_aggrs
            if (
                (
                    batch_name is None
                    or aggr.batch_name is not None
                    and batch_name in aggr.batch_name
                )
                and (
                    batch_status is None
                    or aggr.batch_state in [BatchState(s) for s in batch_status]
                )
                and (
                    breed_type is None
                    or any(breed_type in breed.chicken_breed for breed in aggr.breeds)
                )
                and (
                    period is None
                    or (
                        aggr.cycle_date[0] <= period[1]
                        and (
                            aggr.cycle_date[1] is None
                            or aggr.cycle_date[1] >= period[0]
                        )
                    )
                )
            )
        ]

    def get_not_completed_batches_summary(
        self, all_aggrs: list[BatchAggregate]
    ) -> list[BatchAggregate]:
        """獲取未結案的批次列表

        Args:
            all_aggrs (list[BatchAggregate]): 所有批次聚合

        Returns:
            list[BatchAggregate]: 未結案批次列表
        """
        try:
            filtered_aggrs = [
                aggr
                for aggr in all_aggrs
                if aggr.batch_state
                in [
                    BatchState.BREEDING,
                    BatchState.SALE,
                ]
            ]
            return filtered_aggrs
        except Exception as e:
            logger.error(f"獲取未結案批次時發生錯誤: {e}")
            raise ValueError(f"獲取未結案批次時發生錯誤: {str(e)}")
