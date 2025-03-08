from typing import List

from sqlmodel import Session, and_, select

from src.cleansales_refactor import ProcessingEvent
from src.cleansales_refactor.domain.models import SaleRecord
from src.cleansales_refactor.exporters import SaleRecordORM


class SaleRepository:
    def __init__(self, session: Session):
        self.session = session

    def get_sales_by_location(self, location: str) -> List[SaleRecord]:
        stmt = select(SaleRecordORM).where(
            and_(
                SaleRecordORM.location == location,
                SaleRecordORM.event == ProcessingEvent.ADDED,
            )
        )
        sales_orm = self.session.exec(stmt).all()
        return [
            SaleRecord(
                **{
                    k: v
                    for k, v in orm.__dict__.items()
                    if k in SaleRecord.__annotations__
                }
            )
            for orm in sales_orm
        ]
