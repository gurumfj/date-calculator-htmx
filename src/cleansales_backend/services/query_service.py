import logging
from collections import defaultdict
from datetime import datetime
from functools import lru_cache
from typing import Literal

from sqlmodel import Session
from typing_extensions import Any

from cleansales_backend.core import Event
from cleansales_backend.core.database import Database
from cleansales_backend.core.event_bus import EventBus
from cleansales_backend.core.events import SystemEvent
from cleansales_backend.domain import utils
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
    _event_bus: EventBus

    def __init__(
        self,
        breed_repository: BreedRepositoryProtocol,
        sale_repository: SaleRepositoryProtocol,
        feed_repository: FeedRepositoryProtocol,
        db: Database,
        event_bus: EventBus,
    ) -> None:
        self._breed_repository = breed_repository
        self._sale_repository = sale_repository
        self._feed_repository = feed_repository
        self._db = db
        self._db_hint = {datetime.now().isoformat(): "Started"}
        self._event_bus = event_bus
        self._event_bus.register(SystemEvent.CACHE_CLEAR, self.event_clear_cache)

    def event_clear_cache(self, event: Event) -> None:
        if event.event == SystemEvent.CACHE_CLEAR:
            self.cache_clear()

    def get_batch_cache_info(self) -> dict[str, Any]:
        cache_info = {
            "get_batch_aggregates_cache_info": self.get_batch_aggregates.cache_info()._asdict(),  # noqa: E501
            "db session hint": self._db_hint,
        }
        return cache_info

    def cache_clear(self) -> None:
        logger.info("Cleaning cached data")
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
        all_aggregates: list[BatchAggregate],
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
            aggregate
            for aggregate in all_aggregates
            if (
                (
                    batch_name is None
                    or aggregate.batch_name is not None
                    and batch_name in aggregate.batch_name
                )
                and (
                    batch_status is None
                    or aggregate.batch_state in [BatchState(s) for s in batch_status]
                )
                and (
                    breed_type is None
                    or any(
                        breed_type in breed.chicken_breed for breed in aggregate.breeds
                    )
                )
                and (
                    period is None
                    or (
                        aggregate.cycle_date[0] <= period[1]
                        and (
                            aggregate.cycle_date[1] is None
                            or aggregate.cycle_date[1] >= period[0]
                        )
                    )
                )
            )
        ]

    def get_paginated_sales_data(
        self,
        all_aggregates: list[BatchAggregate],
        page: int = 1,
        page_size: int = 100,
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
        sort_by: str | None = None,
        sort_desc: bool = False,
    ) -> tuple[list[dict[str, Any]], dict[str, int]]:
        """獲取分頁的銷售數據

        返回適合Excel/Google Apps Script使用的格式化銷售數據

        Args:
            all_aggregates: 所有批次聚合
            page: 當前頁碼，從1開始
            page_size: 每頁記錄數量
            batch_name: 批次名稱過濾條件
            breed_type: 雞種類型過濾條件
            batch_status: 批次狀態過濾條件
            period: 時間範圍過濾條件
            sort_by: 排序字段
            sort_desc: 是否降序排序

        Returns:
            tuple[list[dict], dict]: 包含銷售記錄列表和分頁信息的元組
        """
        from cleansales_backend.domain.models.excel_sale_record import ExcelSaleRecord

        # 首先按條件過濾批次
        filtered_aggregates = self.get_batch_aggregates_by_criteria(
            all_aggregates, batch_name, breed_type, batch_status, period
        )

        # 從批次中收集所有銷售記錄並格式化
        all_sales: list[dict[str, Any]] = []
        for aggregate in filtered_aggregates:
            if not aggregate.sales:
                continue

            for sale in aggregate.sales:
                excel_sale = ExcelSaleRecord.create_from_sale_and_batch(
                    sale=sale,
                    batch_name=aggregate.batch_name or "",
                    farm_name=aggregate.farm_name,
                    breed_type=aggregate.breeds[0].chicken_breed,
                    breed_date=aggregate.breeds[0].breed_date,
                    day_age=[
                        utils.day_age(breed.breed_date, sale.sale_date)
                        for breed in sorted(
                            aggregate.breeds, key=lambda x: x.breed_date
                        )
                    ],
                )
                all_sales.append(excel_sale.model_dump(mode="json"))

        # 排序
        if sort_by:
            reverse = sort_desc
            all_sales.sort(key=lambda x: x.get(sort_by, ""), reverse=reverse)

        # 計算分頁信息
        total = len(all_sales)
        total_pages = (total + page_size - 1) // page_size if total > 0 else 1

        # 確保頁碼在有效範圍內
        page = max(1, min(page, total_pages))

        # 選擇當前頁的數據
        start_idx = (page - 1) * page_size
        end_idx = min(start_idx + page_size, total)
        page_data = all_sales[start_idx:end_idx]

        # 構建分頁信息
        pagination = {
            "page": page,
            "page_size": page_size,
            "total": total,
            "total_pages": total_pages,
        }

        return page_data, pagination

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
