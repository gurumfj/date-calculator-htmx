import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

import pandas as pd

from ..domain.models import BatchAggregate, BatchState
from ..shared.models import Response, SourceData

logger = logging.getLogger(__name__)


@dataclass
class QueryFilter:
    """查詢過濾條件"""

    batch_name: str | None = None
    breed_type: str | None = None
    status: Literal["all", "completed", "breeding", "sale"] = "all"


class CLIService:
    """CLI 命令處理服務

    處理命令列介面的各項操作，包含：
    1. 匯入銷售資料
    2. 匯入品種資料
    3. 查詢品種資料
    """

    def import_sales(self, file_path: str | Path, check_md5: bool = True) -> Response:
        """匯入銷售資料"""
        source_data = SourceData(
            file_name=str(file_path), dataframe=pd.read_excel(file_path)
        )
        with self.db.get_session() as session:
            return self.clean_sales_service.execute_clean_sales(
                session, source_data, check_exists=check_md5
            )

    def import_breeds(self, file_path: str | Path, check_md5: bool = True) -> Response:
        """匯入品種資料"""
        source_data = SourceData(
            file_name=str(file_path), dataframe=pd.read_excel(file_path)
        )
        with self.db.get_session() as session:
            return self.clean_sales_service.execute_clean_breeds(
                session, source_data, check_exists=check_md5
            )

    @staticmethod
    def _filter_aggregates(
        aggregates: list[BatchAggregate], filter_: QueryFilter
    ) -> list[BatchAggregate]:
        """純函數：過濾批次聚合數據

        Args:
            aggregates: 原始聚合數據
            filter_: 過濾條件

        Returns:
            過濾後的聚合數據
        """
        result = aggregates

        if filter_.batch_name:
            result = [
                aggr
                for aggr in result
                if aggr.batch_name and filter_.batch_name in aggr.batch_name
            ]

        if filter_.breed_type:
            result = [
                aggr
                for aggr in result
                if aggr.chicken_breed and filter_.breed_type in aggr.chicken_breed
            ]

        if filter_.status != "all":
            state_map = {
                "completed": BatchState.COMPLETED,
                "breeding": BatchState.BREEDING,
                "sale": BatchState.SALE,
            }
            if state := state_map.get(filter_.status):
                result = [aggr for aggr in result if aggr.batch_state == state]

        return result

    def query_breeds(
        self,
        aggrs: list[BatchAggregate],
        batch_name: str | None = None,
        breed_type: str | None = None,
        status: Literal["all", "completed", "breeding", "sale"] = "all",
    ) -> list[BatchAggregate]:
        """查詢品種資料"""
        try:
            filter_ = QueryFilter(batch_name, breed_type, status)
            filtered_aggrs = self._filter_aggregates(aggrs, filter_)
            return filtered_aggrs
        except Exception as e:
            logger.error(f"篩選批次聚合資料時發生錯誤: {e}")
            raise ValueError(f"查詢失敗: {str(e)}")

    # def query_sales(self, limit: int = 100, offset: int = 0) -> str:
    # TODO: 需要建構獲取 raw sales data 的 presentation layer
    #     """查詢銷售資料"""
    #     with self.db.get_session() as session:

    #         result = self.query_service.get_sales_data(
    #             session, limit=limit, offset=offset
    #         )
    #         msg = []
    #         for sale in result:
    #             msg.append(str(sale))
    #             msg.append("-" * 88)
    #         msg.append(f"共 {len(result)} 筆記錄")
    #         return "\n".join(msg)
