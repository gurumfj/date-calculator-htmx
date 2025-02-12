from typing import List

from sqlmodel import Session, select

from cleansales_refactor.domain.models import SaleRecord
from cleansales_refactor.exporters import SaleRecordORM


class SaleRepository:
    def __init__(self, session: Session):
        self.session = session

    def get_sales_by_location(self, location: str) -> List[SaleRecord]:
        stmt = select(SaleRecordORM).where(SaleRecordORM.location == location)
        sales_orm = self.session.exec(stmt).all()
        return [
            SaleRecord(**{
                k: v
                for k, v in orm.__dict__.items()
                if k in SaleRecord.__annotations__
            })
            for orm in sales_orm
        ]
