from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Generic, TypeAlias, TypeVar

Location: TypeAlias = str


@dataclass
class SaleRecord:
    """銷售記錄資料模型"""

    closed: str | None
    handler: str | None
    date: datetime
    location: str
    customer: str
    male_count: int
    female_count: int
    total_weight: float | None
    total_price: float | None
    male_price: float | None
    female_price: float | None
    unpaid: str | None


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
