from pathlib import Path

import pandas as pd

from ..exporters import Database
from ..shared.models import Response, SourceData
from .cleansales_service import CleanSalesService


class DataService:
    def __init__(self, db_path: str | Path):
        self.db = Database(str(db_path))
        self.clean_sales_service = CleanSalesService()

    def sales_data_service(
        self, file_path: str | Path, check_md5: bool = True
    ) -> Response:
        source_data = SourceData(
            file_name=str(file_path), dataframe=pd.read_excel(file_path)
        )
        with self.db.get_session() as session:
            return self.clean_sales_service.execute_clean_sales(
                session, source_data, check_exists=check_md5
            )

    def breeds_data_service(
        self, file_path: str | Path, check_md5: bool = True
    ) -> Response:
        source_data = SourceData(
            file_name=str(file_path), dataframe=pd.read_excel(file_path)
        )
        with self.db.get_session() as session:
            return self.clean_sales_service.execute_clean_breeds(
                session, source_data, check_exists=check_md5
            )
