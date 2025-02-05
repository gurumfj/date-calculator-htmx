import hashlib
from dataclasses import dataclass, field, replace
from datetime import datetime
from typing import Any, Generic, TypeVar

import pandas as pd


@dataclass(frozen=True)
class ErrorMessage:
    message: str
    data: dict[str, Any]
    extra: dict[str, Any]
    timestamp: str = field(
        default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    )


T = TypeVar("T")


@dataclass(frozen=True)
class SourceData:
    file_name: str
    dataframe: pd.DataFrame

    @property
    def md5(self) -> str:
        return hashlib.md5(
            self.dataframe.to_csv(index=False).encode("utf-8")
        ).hexdigest()


@dataclass(frozen=True)
class ProcessingResult(Generic[T]):
    """處理結果的不可變資料類別"""

    processed_data: list[T]
    errors: list[ErrorMessage]
    source_data: SourceData
    
    def with_updates(self, **updates: Any) -> "ProcessingResult[T]":
        return replace(self, **updates)


@dataclass(frozen=True)
class ProcessorPipelineData(Generic[T]):
    source_data: SourceData
    process_result: ProcessingResult[T]
    exporter_result: dict[str, Any]

    def with_updates(self, **updates: Any) -> "ProcessorPipelineData[T]":
        return replace(self, **updates)
