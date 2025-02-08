import logging

import pandas as pd
from sqlmodel import Session, and_, asc, or_, select

from cleansales_refactor import CleanSalesDomainService, CleanSalesService, SourceData
from cleansales_refactor.domain.models import BreedRecord
from cleansales_refactor.exporters import BreedRecordORM, ProcessingEvent
from event_bus import Event, EventBus
from fastapi import Depends, UploadFile

from ..core.database import get_session
from ..core.event_bus import get_event_bus
from ..core.events import ProcessEvent as ApiProcessEvent
from ..models.breed import (
    BatchGroupBreedResponseModel,
    BreedInfo,
)
from ..models.response import ResponseModel

logger = logging.getLogger(__name__)


class PostApiDependency:
    def __init__(self, event_bus: EventBus, session: Session) -> None:
        self.service = CleanSalesService()
        self.domain_service = CleanSalesDomainService()
        self.event_bus = event_bus
        self.session = session

    def sales_processpipline(self, upload_file: UploadFile) -> ResponseModel:
        source_data = SourceData(
            file_name=upload_file.filename or "",
            dataframe=pd.read_excel(upload_file.file),
        )
        result = self.service.execute_clean_sales(self.session, source_data)
        if result.status == "success":
            self.event_bus.publish(
                Event(
                    event=ApiProcessEvent.SALES_PROCESSING_COMPLETED,
                    content={"msg": result.msg},
                )
            )
        return ResponseModel(
            status=result.status,
            msg=result.msg,
            content=result.content,
        )

    def breed_processpipline(self, upload_file: UploadFile) -> ResponseModel:
        source_data = SourceData(
            file_name=upload_file.filename or "",
            dataframe=pd.read_excel(upload_file.file),
        )
        result = self.service.execute_clean_breeds(self.session, source_data)
        if result.status == "success":
            self.event_bus.publish(
                Event(
                    event=ApiProcessEvent.BREEDS_PROCESSING_COMPLETED,
                    content={"msg": result.msg},
                )
            )
        return ResponseModel(
            status=result.status,
            msg=result.msg,
            content=result.content,
        )

    def get_breeds_is_not_completed(self) -> ResponseModel:
        stmt = (
            select(BreedRecordORM)
            .where(
                and_(
                    or_(
                        BreedRecordORM.is_completed != "結場",
                        BreedRecordORM.is_completed == None,
                    ),
                    BreedRecordORM.event == ProcessingEvent.ADDED,
                )
            )
            .order_by(asc(BreedRecordORM.breed_date))
        )
        breeds_orm = self.session.exec(stmt).all()
        breeds = [
            BreedRecord(**{
                k: v
                for k, v in orm.__dict__.items()
                if k in BreedRecord.__annotations__
            })
            for orm in breeds_orm
        ]

        breed_data = self.domain_service.group_by_batch(breeds)
        response_data = [
            BatchGroupBreedResponseModel(
                batch_name=batch.batch_name,
                farm_name=batch.farm_name,
                address=batch.address,
                farmer_name=batch.farmer_name,
                total_male=batch.total_male,
                total_female=batch.total_female,
                veterinarian=batch.veterinarian,
                is_completed=batch.is_completed,
                breeds_info=[
                    BreedInfo(
                        breed_date=breed.breed_date,
                        supplier=breed.supplier,
                        chicken_breed=breed.chicken_breed,
                        male=breed.male,
                        female=breed.female,
                    )
                    for breed in batch.breeds_info
                ],
            )
            for batch in breed_data
        ]

        return ResponseModel(
            status="success",
            msg=f"成功取得未結場入雛資料 {len(breeds)} 筆",
            content={"batches": [batch.model_dump() for batch in response_data]},
        )


def get_api_dependency(
    event_bus: EventBus = Depends(get_event_bus),
    session: Session = Depends(get_session),
) -> PostApiDependency:
    return PostApiDependency(event_bus=event_bus, session=session)
