from dataclasses import dataclass
from datetime import datetime

from .batch_state import BatchState


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

    @property
    def sale_state(self) -> BatchState:
        return BatchState.COMPLETED if self.closed == "結案" else BatchState.SALE

    def __str__(self) -> str:
        msg = []
        for k, v in self.__dict__.items():
            msg.append(f"{k}: {v}")
        return "\n".join(msg)
