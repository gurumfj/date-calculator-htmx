import logging
from typing import Generic, Protocol, TypeVar

import pandas as pd

from ..models import ProcessingResult

logger = logging.getLogger(__name__)

T = TypeVar("T")
class DataSourceReader(Protocol):
    """定義資料來源讀取介面"""

    def read_data(self) -> pd.DataFrame:
        """讀取資料"""
        ...


class IProcessor(Protocol, Generic[T]):
    """定義資料處理介面"""

    def process_data(self, data: pd.DataFrame) -> ProcessingResult[T]:
        """處理資料"""
        ...


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


class BaseDataService(Generic[T]):
    """銷售記錄資料匯入器

    負責處理原始銷售資料，並透過指定的匯出器匯出結果。

    Attributes:
        _processing_result: 儲存處理結果，包含成功處理的資料與錯誤資料
        _exporter: 實作 IExporter 介面的匯出器實例
    """

    def __init__(
        self,
        processor: IProcessor[T],
        exporter: IExporter[T],
        data_reader: DataSourceReader,
    ) -> None:
        self._data_reader = data_reader
        self._processing_result: ProcessingResult[T] = ProcessingResult(
            processed_data=[], errors=[]
        )
        self._processor = processor
        self._exporter = exporter

    def execute(self) -> None:
        """執行資料處理，修改內部狀態"""
        data = self._data_reader.read_data()
        self._processing_result = self._processor.process_data(data)
        self._exporter.export_data(self._processing_result)
        self._exporter.export_errors(self._processing_result)

    # def export_data(self) -> None:
    #     """將處理後的資料匯出為 excel"""

    # def export_errors(self) -> None:
    #     """將錯誤資料匯出為 excel"""
