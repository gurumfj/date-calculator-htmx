import logging
from pathlib import Path
from typing import Any, Callable

import pandas as pd

from cleansales_refactor.exporters import (
    BreedSQLiteExporter,
    Database,
    SaleSQLiteExporter,
)
from cleansales_refactor.models.shared import (
    SourceData,
    ProcessingResult,
)
from cleansales_refactor.processor import BreedsProcessor, SalesProcessor

# 設定根 logger
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)

logger = logging.getLogger(__name__)

# 確保其他模組的 logger 也設定為 DEBUG 級別
logging.getLogger("cleansales_refactor").setLevel(logging.DEBUG)


class DataService:
    def __init__(self, db_path: str | Path):
        self.db = Database(str(db_path))
        self.sales_exporter = SaleSQLiteExporter()
        self.breeds_exporter = BreedSQLiteExporter()

    def sales_data_service(self, file_path: str | Path) -> dict[str, Any]:
        source_data = SourceData(
            file_name=str(file_path), dataframe=pd.read_excel(file_path)
        )
        processor: Callable[[SourceData], ProcessingResult[Any]] = (
            lambda source_data: SalesProcessor.execute(source_data)
        )

        with self.db.get_session() as session:
            if self.sales_exporter.is_source_md5_exists_in_latest_record(
                session, source_data
            ):
                logger.debug(f"販售資料 md5 {source_data.md5} 已存在")
                return dict(status="error", msg="販售資料已存在", content={})
            else:
                return self.sales_exporter.execute(session, processor(source_data))

    def breeds_data_service(self, file_path: str | Path) -> dict[str, Any]:
        source_data = SourceData(
            file_name=str(file_path), dataframe=pd.read_excel(file_path)
        )
        processor: Callable[[SourceData], ProcessingResult[Any]] = (
            lambda source_data: BreedsProcessor.execute(source_data)
        )

        with self.db.get_session() as session:
            if self.breeds_exporter.is_source_md5_exists_in_latest_record(
                session, source_data
            ):
                logger.debug(f"品種資料 md5 {source_data.md5} 已存在")
                return dict(status="error", msg="品種資料已存在", content={})
            else:
                return self.breeds_exporter.execute(session, processor(source_data))


if __name__ == "__main__":
    data_service = DataService("data.db")
    print(data_service.sales_data_service("/app/data/sales_sample.xlsx"))
    print(data_service.breeds_data_service("/app/data/breeds_sample.xlsx"))
