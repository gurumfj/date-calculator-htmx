from typing import Generic, Protocol, TypeVar

from sqlmodel import Session

from ..shared.models import ProcessingResult, SourceData

T = TypeVar("T")


class IExporter(Protocol, Generic[T]):
    """定義資料匯出介面"""

    def execute(
        self,
        result: ProcessingResult[T],
        session: Session | None = None,
    ) -> dict[str, int]:
        """匯出處理後的資料

        Args:
            result: 包含處理後資料與錯誤的結果物件
        """
        ...

    def is_source_md5_exists_in_latest_record(
        self, session: Session, source_data: SourceData
    ) -> bool:
        """檢查 md5 是否存在"""
        ...
