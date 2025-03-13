from datetime import datetime
from typing import Literal, Protocol, runtime_checkable

from sqlmodel import Session, and_, col, select
from typing_extensions import override

from cleansales_refactor.domain.models import SaleRecord
from cleansales_refactor.exporters import ProcessingEvent, SaleRecordORM


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


class SaleRepository(SaleRepositoryProtocol):
    """銷售記錄倉儲實現"""

    def _orm_to_domain(self, orm: SaleRecordORM) -> SaleRecord:
        """將 ORM 轉換為 Domain 模型"""
        return SaleRecord(
            **{k: v for k, v in orm.__dict__.items() if k in SaleRecord.__annotations__}
        )

    @override
    def get_sales_by_location(
        self, session: Session, location: str
    ) -> list[SaleRecord]:
        """根據場別查詢銷售記錄"""
        statement = select(SaleRecordORM).where(
            and_(
                SaleRecordORM.event == ProcessingEvent.ADDED.value,
                SaleRecordORM.location == location,
            )
        )
        sales_orm = session.exec(statement).all()
        return [self._orm_to_domain(orm) for orm in sales_orm]

    @override
    def get_sales_data(
        self, session: Session, limit: int = 300, offset: int = 0
    ) -> list[SaleRecord]:
        """獲取銷售記錄"""
        stmt = (
            select(SaleRecordORM)
            .where(SaleRecordORM.event == ProcessingEvent.ADDED.value)
            .order_by(col(SaleRecordORM.sale_date).desc())
            .offset(offset)
            .limit(limit)
        )
        sales_orm = session.exec(stmt).all()
        return [self._orm_to_domain(orm) for orm in sales_orm]

    def _get_sales_by_criteria(
        self,
        session: Session,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        location: str | None = None,
        condition: Literal["like", "eq"] = "like",
    ) -> list[SaleRecord]:
        """根據條件獲取銷售記錄

        Args:
            start_date (Optional[datetime]): 開始日期
            end_date (Optional[datetime]): 結束日期
            location (Optional[str]): 場別

        Returns:
            list[SaleRecord]: 符合條件的銷售記錄列表
        """
        stmt = select(SaleRecordORM).where(
            SaleRecordORM.event == ProcessingEvent.ADDED.value
        )

        if start_date:
            stmt = stmt.where(SaleRecordORM.sale_date >= start_date)
        if end_date:
            stmt = stmt.where(SaleRecordORM.sale_date <= end_date)
        if location and condition == "like":
            stmt = stmt.where(col(SaleRecordORM.location).contains(location))
        elif location and condition == "eq":
            stmt = stmt.where(SaleRecordORM.location == location)

        sales_orm = session.exec(stmt).all()
        return [self._orm_to_domain(orm) for orm in sales_orm]

    def get_unpaid_sales(self, session: Session) -> list[SaleRecord]:
        """獲取未付款的銷售記錄

        Returns:
            list[SaleRecord]: 未付款的銷售記錄列表
        """
        stmt = select(SaleRecordORM).where(
            and_(
                SaleRecordORM.event == ProcessingEvent.ADDED.value,
                col(SaleRecordORM.unpaid).is_not(None),
            )
        )

        sales_orm = session.exec(stmt).all()
        return [self._orm_to_domain(orm) for orm in sales_orm]
