import pandas as pd

from cleansales_refactor.models.sale_record import ProcessingResult
from cleansales_refactor.services import IExporter

from ..models import SaleRecord


class ExcelExporter(IExporter[SaleRecord]):
    """Excel 匯出服務"""

    def __init__(self, export_file_path: str, errors_file_path: str) -> None:
        self._export_file_path = export_file_path
        self._errors_file_path = errors_file_path

    def export_data(self, result: ProcessingResult[SaleRecord]) -> None:
        """將處理結果匯出為 Excel"""
        if not result.processed_data:
            raise ValueError("No grouped data to export")

        df = pd.DataFrame([record for record in result.processed_data])
        df.to_excel(self._export_file_path, index=False)

    def export_errors(self, result: ProcessingResult[SaleRecord]) -> None:
        """將錯誤資料匯出為 Excel"""
        df = pd.DataFrame([error for error in result.errors])
        df.to_excel(self._errors_file_path, index=False)
