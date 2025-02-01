from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
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
