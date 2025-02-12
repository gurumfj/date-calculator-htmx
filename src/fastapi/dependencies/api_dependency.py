import logging
from collections import defaultdict

import pandas as pd
from sqlmodel import Session

from cleansales_refactor import CleanSalesDomainService, CleanSalesService, SourceData
from cleansales_refactor.domain.models import BatchAggregate, BreedRecord
from event_bus import Event, EventBus
from fastapi import Depends, UploadFile

from ..core.database import get_session
from ..core.event_bus import get_event_bus
from ..core.events import ProcessEvent as ApiProcessEvent
from ..models.breed import (
    BatchAggregateModel,
)
from ..models.response import BatchAggregateResponseModel, ResponseModel
from ..repositories.breed_repository import BreedRepository
from ..repositories.sale_repository import SaleRepository

logger = logging.getLogger(__name__)


class PostApiDependency:
    def __init__(self, event_bus: EventBus, session: Session) -> None:
        self.service = CleanSalesService()
        self.domain_service = CleanSalesDomainService()
        self.event_bus = event_bus
        self.session = session
        self.breed_repository = BreedRepository(session)
        self.sale_repository = SaleRepository(session)

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

    def get_breeds_is_not_completed(self) -> BatchAggregateResponseModel:
        batch_aggregates: list[BatchAggregate] = []
        breed_records_dict: dict[str, list[BreedRecord]] = defaultdict(list)
        breeds: list[BreedRecord] = self.breed_repository.get_not_completed_breeds()
        for breed in breeds:
            breed_records_dict[breed.batch_name].append(breed)

        for batch_name, breeds in breed_records_dict.items():
            sales = self.sale_repository.get_sales_by_location(batch_name)
            batch_aggregates.append(BatchAggregate(breeds=breeds, sales=sales))

        response_data = [
            BatchAggregateModel(
                batch_name=batch.batch_name,
                farm_name=batch.farm_name,
                address=batch.address,
                farmer_name=batch.farmer_name,
                total_male=batch.total_male,
                total_female=batch.total_female,
                veterinarian=batch.veterinarian,
                batch_state=batch.batch_state,
                breed_date=batch.breed_date,
                supplier=batch.supplier,
                chicken_breed=batch.chicken_breed,
                male=batch.male,
                female=batch.female,
                day_age=batch.day_age,
                week_age=batch.week_age,
            )
            for batch in batch_aggregates
        ]

        return BatchAggregateResponseModel(
            status="success",
            msg="Successfully retrieved incomplete breeds",
            content={"count": len(response_data), "batches": response_data},
        )


def get_api_dependency(
    event_bus: EventBus = Depends(get_event_bus),
    session: Session = Depends(get_session),
) -> PostApiDependency:
    return PostApiDependency(event_bus=event_bus, session=session)
