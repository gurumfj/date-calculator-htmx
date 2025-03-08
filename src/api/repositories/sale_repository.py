from typing import List

from sqlmodel import Session, and_, select

from cleansales_refactor.domain.models import SaleRecord
from cleansales_refactor.exporters import SaleRecordORM
from cleansales_refactor import ProcessingEvent

class SaleRepository:
    def __init__(self, session: Session):
        self.session = session

    def get_sales_by_location(self, location: str) -> List[SaleRecord]:
        stmt = select(SaleRecordORM).where(and_(
            SaleRecordORM.location == location,
            SaleRecordORM.event == ProcessingEvent.ADDED,
        ))
        sales_orm = self.session.exec(stmt).all()
        return [
            SaleRecord(**{
                k: v
                for k, v in orm.__dict__.items()
                if k in SaleRecord.__annotations__
            })
            for orm in sales_orm
        ]
