import logging
from typing import Protocol

import pandas as pd

from cleansales_refactor.models import ProcessingResult
from cleansales_refactor.services import SaleRecordProcessor

logger = logging.getLogger(__name__)


class IExporter(Protocol):
    def export_data(self, result: ProcessingResult) -> None: ...

    def export_errors(self, result: ProcessingResult) -> None: ...


class SaleRecordRawDataImporter:
    """銷售記錄資料匯入器"""

    def __init__(self, exporter: IExporter) -> None:
        self._processing_result: ProcessingResult = ProcessingResult([], [])
        self._exporter = exporter

    def execute(self, data: pd.DataFrame) -> None:
        """執行資料處理，修改內部狀態"""
        self._processing_result = SaleRecordProcessor.process_data(data)

    def export_data(self) -> None:
        """將處理後的資料匯出為 excel"""
        self._exporter.export_data(self._processing_result)

    def export_errors(self) -> None:
        """將錯誤資料匯出為 excel"""
        self._exporter.export_errors(self._processing_result)
