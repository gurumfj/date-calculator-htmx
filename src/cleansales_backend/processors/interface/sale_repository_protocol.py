from typing import Protocol, runtime_checkable

from sqlmodel import Session

from cleansales_backend.domain.models import SaleRecord


@runtime_checkable
class SaleRepositoryProtocol(Protocol):
    """銷售記錄倉儲協議"""

    def get_sales_by_location(
        self, session: Session, location: str
    ) -> list[SaleRecord]:
        """根據場別查詢銷售記錄"""
        ...

    def get_sales_data(
        self, session: Session, limit: int = 300, offset: int = 0
    ) -> list[SaleRecord]:
        """獲取銷售記錄"""
        ...
