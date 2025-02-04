from typing import Any, Generic, Protocol, TypeVar

from cleansales_refactor.models import ProcessingResult, SourceData

T = TypeVar("T")


class IExporter(Protocol, Generic[T]):
    """定義資料匯出介面"""

    def export_data(self, source_data: SourceData, result: ProcessingResult[T]) -> dict[str, str]:
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

    def is_source_md5_exists_in_latest_record(self, source_md5: str) -> bool:
        """檢查 md5 是否存在"""
        ...
