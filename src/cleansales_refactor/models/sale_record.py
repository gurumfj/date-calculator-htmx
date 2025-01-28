from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, TypeAlias

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
    _date_diff: float = field(default=0)
    _group_id: int = field(default=0)


@dataclass
class SaleRecordsGroupByLocation:
    """按位置分組的銷售記錄"""

    location: str
    sale_records: list[SaleRecord]

@dataclass
class ErrorMessage:
    message: str
    data: dict[str, Any]
    extra: dict[str, Any]
    timestamp: str = field(
        default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    )


@dataclass
class ProcessingResult:
    """處理結果的不可變資料類別"""

    grouped_data: list[SaleRecordsGroupByLocation]
    errors: list[ErrorMessage]
