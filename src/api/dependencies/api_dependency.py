import logging
from collections import defaultdict

import pandas as pd
from fastapi import UploadFile
from sqlmodel import Session

from src.cleansales_refactor import CleanSalesService, SourceData
from src.cleansales_refactor.domain.models import BatchAggregate, BreedRecord

from ...core.event_bus import Event, EventBus
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
            self._batch_aggregate_to_model(batch) for batch in batch_aggregates
        ]

        return BatchAggregateResponseModel(
            status="success",
            msg="Successfully retrieved incomplete breeds",
            content={"count": len(response_data), "batches": response_data},
        )

    def get_breeds_by_batch_name(self, batch_name: str) -> BatchAggregateResponseModel:
        breeds = self.breed_repository.get_breeds_by_batch_name(batch_name)
        sales = self.sale_repository.get_sales_by_location(batch_name)
        batch_aggregate = BatchAggregate(breeds=breeds, sales=sales)
        response_data = [self._batch_aggregate_to_model(batch_aggregate)]
        return BatchAggregateResponseModel(
            status="success",
            msg="Successfully retrieved breeds by batch name",
            content={"count": len(response_data), "batches": response_data},
        )

    def _batch_aggregate_to_model(
        self, batch_aggregate: BatchAggregate
    ) -> BatchAggregateModel:
        return BatchAggregateModel(
            batch_name=batch_aggregate.batch_name,
            farm_name=batch_aggregate.farm_name,
            address=batch_aggregate.address,
            farmer_name=batch_aggregate.farmer_name,
            total_male=batch_aggregate.total_male,
            total_female=batch_aggregate.total_female,
            veterinarian=batch_aggregate.veterinarian,
            batch_state=batch_aggregate.batch_state,
            breed_date=batch_aggregate.breed_date,
            supplier=batch_aggregate.supplier,
            chicken_breed=batch_aggregate.chicken_breed,
            male=batch_aggregate.male,
            female=batch_aggregate.female,
            day_age=batch_aggregate.day_age,
            week_age=batch_aggregate.week_age,
            sales_male=batch_aggregate.sales_male,
            sales_female=batch_aggregate.sales_female,
            total_sales=batch_aggregate.total_sales,
            sales_percentage=batch_aggregate.sales_percentage,
        )


# def get_api_dependency(
#     event_bus: EventBus = Depends(get_event_bus),
#     session: Session = Depends(get_session),
# ) -> PostApiDependency:
#     return PostApiDependency(event_bus=event_bus, session=session)
