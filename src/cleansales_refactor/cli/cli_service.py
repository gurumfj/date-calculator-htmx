import logging
from pathlib import Path

import pandas as pd

from ..core import Database
from ..services import CleanSalesService, QueryService
from ..shared.models import Response, SourceData

logger = logging.getLogger(__name__)


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
        self.query_service = QueryService()

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

    def query_breeds(self, breed_type: str = "all") -> str:
        """查詢未完成的品種資料"""

        with self.db.get_session() as session:
            result = self.query_service.get_breeds_is_not_completed(session)
            if not result:
                return "未找到符合條件的記錄"

            msg = []

            if breed_type == "all":
                msg = [str(batch) for batch in result]
                chicken_breeds_set = set([batch.chicken_breed[0] for batch in result])
                logger.debug(f"chicken_breeds_set: {chicken_breeds_set}")
                for chicken_breed in chicken_breeds_set:
                    msg.extend(
                        [
                            f"{chicken_breed}: {
                                len(
                                    [
                                        batch
                                        for batch in result
                                        if chicken_breed in batch.chicken_breed
                                    ]
                                )
                            } 批次"
                        ]
                    )
            else:
                msg = [
                    str(batch) for batch in result if breed_type in batch.chicken_breed
                ]
                msg.append(f"批次: {len(msg)} 批次")

            return "\n".join(msg)
