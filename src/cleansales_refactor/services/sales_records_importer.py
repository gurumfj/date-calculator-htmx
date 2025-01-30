import logging
from typing import Generic, Protocol, TypeVar

import pandas as pd

from ..models import ProcessingResult, SaleRecord
from ..processor import SalesProcessor

logger = logging.getLogger(__name__)

T = TypeVar("T")

class IExporter(Protocol, Generic[T]):
    """定義資料匯出介面"""

    def export_data(self, result: ProcessingResult[T]) -> None:
        """匯出處理後的資料

        Args:
            result: 包含處理後資料與錯誤的結果物件
        """
        ...

    def export_errors(self, result: ProcessingResult[T]) -> None:
        """匯出錯誤資料

        Args:
            result: 包含處理後資料與錯誤的結果物件
        """
        ...


class SaleRecordRawDataImporter:
    """銷售記錄資料匯入器

    負責處理原始銷售資料，並透過指定的匯出器匯出結果。

    Attributes:
        _processing_result: 儲存處理結果，包含成功處理的資料與錯誤資料
        _exporter: 實作 IExporter 介面的匯出器實例
    """

    def __init__(self, exporter: IExporter[SaleRecord]) -> None:
        self._processing_result: ProcessingResult[SaleRecord] = ProcessingResult(
            processed_data=[], errors=[]
        )
        self._exporter = exporter

    def execute(self, data: pd.DataFrame) -> None:
        """執行資料處理，修改內部狀態"""
        self._processing_result = SalesProcessor.process_data(data)

    def export_data(self) -> None:
        """將處理後的資料匯出為 excel"""
        self._exporter.export_data(self._processing_result)

    def export_errors(self) -> None:
        """將錯誤資料匯出為 excel"""
        self._exporter.export_errors(self._processing_result)
