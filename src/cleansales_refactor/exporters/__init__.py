from typing import Generic, Protocol, TypeVar

from cleansales_refactor.models import ProcessingResult

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

__all__ = ["ExcelExporter", "IExporter"]