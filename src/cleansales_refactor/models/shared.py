from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Generic, TypeVar


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
class ProcessingResult(Generic[T]):
    """處理結果的不可變資料類別"""

    processed_data: list[T]
    errors: list[ErrorMessage]
