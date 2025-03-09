from pathlib import Path
from typing import List

import pandas as pd

from ..domain.models import BreedRecord
from ..exporters.database import Database
from ..repositories.breed_repository import BreedRepository
from ..shared.models import Response, SourceData
from .cleansales_service import CleanSalesService


class CLIService:
    """CLI 命令處理服務

    處理命令列介面的各項操作，包含：
    1. 匯入銷售資料
    2. 匯入品種資料
    3. 查詢品種資料
    """

    def __init__(self, db_path: str | Path):
        self.db = Database(str(db_path))
        self.clean_sales_service = CleanSalesService()

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

    def query_breeds(self) -> str:
        """查詢未完成的品種資料"""

        def format_breed_records(records: List[BreedRecord]) -> str:
            """
            格式化品種記錄為易讀的表格格式
            """
            if not records:
                return "未找到符合條件的記錄"

            # 計算總數
            total_male = sum(r.male for r in records)
            total_female = sum(r.female for r in records)

            # 格式化每筆記錄
            result = [
                f"查詢到 {len(records)} 筆品種資料",
                f"總公雞數: {total_male:,} 隻",
                f"總母雞數: {total_female:,} 隻",
                f"總計: {total_male + total_female:,} 隻",
                "\n品種資料明細:",
                "=" * 80,
            ]

            for record in records:
                result.extend(
                    [
                        f"批次編號: {record.batch_name}",
                        f"飼養戶: {record.farmer_name}",
                        f"場址: {record.address}",
                        f"品種: {record.chicken_breed}",
                        f"進雞日期: {record.breed_date.strftime('%Y-%m-%d')}",
                        f"公雞數: {record.male:,} 隻",
                        f"母雞數: {record.female:,} 隻",
                        f"獸醫師: {record.veterinarian}",
                        f"完成狀態: {record.is_completed or '未完成'}",
                        "-" * 80,
                    ]
                )

            return "\n".join(result)

        with self.db.get_session() as session:
            breed_repository = BreedRepository(session)
            result = breed_repository.get_not_completed_breeds()
            return format_breed_records(result)
