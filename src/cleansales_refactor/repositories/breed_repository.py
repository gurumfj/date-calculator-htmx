from typing import List

from sqlmodel import Session, and_, asc, or_, select

from cleansales_refactor.domain.models import BreedRecord
from cleansales_refactor.exporters import BreedRecordORM, ProcessingEvent


class BreedRepository:
    def __init__(self, session: Session):
        self.session = session

    def get_not_completed_breeds(self) -> List[BreedRecord]:
        stmt = (
            select(BreedRecordORM)
            .where(
                and_(
                    or_(
                        BreedRecordORM.is_completed != "結場",
                        BreedRecordORM.is_completed == None,
                    ),
                    BreedRecordORM.batch_name != None,
                    BreedRecordORM.event == ProcessingEvent.ADDED,
                )
            )
            .order_by(asc(BreedRecordORM.breed_date))
        )
        breeds_orm = self.session.exec(stmt).all()

        return [
            BreedRecord(
                **{
                    k: v
                    for k, v in orm.__dict__.items()
                    if k in BreedRecord.__annotations__
                }
            )
            for orm in breeds_orm
        ]

    def get_breeds_by_batch_name(self, batch_name: str) -> List[BreedRecord]:
        stmt = select(BreedRecordORM).where(
            and_(
                BreedRecordORM.batch_name.like(f"%{batch_name}%"),
                BreedRecordORM.event == ProcessingEvent.ADDED,
            )
        )
        breeds_orm = self.session.exec(stmt).all()
        return [
            BreedRecord(
                **{
                    k: v
                    for k, v in orm.__dict__.items()
                    if k in BreedRecord.__annotations__
                }
            )
            for orm in breeds_orm
        ]
