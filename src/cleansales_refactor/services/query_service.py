from collections import defaultdict
from typing import List

from sqlmodel import Session

from cleansales_refactor.domain.models import (
    BatchAggregate,
    BatchState,
    BreedRecord,
    SaleRecord,
)
from cleansales_refactor.repositories import BreedRepository, SaleRepository


def group_breeds_by_batch_name(
    breeds: List[BreedRecord],
) -> dict[str, list[BreedRecord]]:
    breed_records_dict: dict[str, list[BreedRecord]] = defaultdict(list)
    for breed in breeds:
        breed_records_dict[breed.batch_name].append(breed)
    return breed_records_dict


def create_batch_aggregates(
    breed_records_dict: dict[str, list[BreedRecord]], sale_repository: SaleRepository
) -> list[BatchAggregate]:
    batch_aggregates: list[BatchAggregate] = []
    for batch_name, breeds in breed_records_dict.items():
        sales = sale_repository.get_sales_by_location(batch_name)
        batch_aggregates.append(BatchAggregate(breeds=breeds, sales=sales))
    return batch_aggregates


class QueryService:
    def get_breeds_is_not_completed(self, session: Session) -> list[BatchAggregate]:
        breed_repository = BreedRepository(session)
        sale_repository = SaleRepository(session)

        breeds = breed_repository.get_not_completed_breeds()
        breed_records_dict = group_breeds_by_batch_name(breeds)
        batch_aggregates = create_batch_aggregates(breed_records_dict, sale_repository)

        return list(
            filter(lambda x: x.batch_state != BatchState.COMPLETED, batch_aggregates)
        )

    def get_breed_by_batch_name(
        self, session: Session, batch_name: str, status: str = "all"
    ) -> list[BatchAggregate]:
        breed_repository = BreedRepository(session)
        sale_repository = SaleRepository(session)

        breeds = breed_repository.get_breeds_by_batch_name(batch_name)
        breed_records_dict = group_breeds_by_batch_name(breeds)
        batch_aggregates = create_batch_aggregates(breed_records_dict, sale_repository)

        match status:
            case "all":
                return batch_aggregates
            case "completed":
                return list(
                    filter(
                        lambda x: x.batch_state == BatchState.COMPLETED,
                        batch_aggregates,
                    )
                )
            case "breeding":
                return list(
                    filter(
                        lambda x: x.batch_state == BatchState.BREEDING, batch_aggregates
                    )
                )
            case "sale":
                return list(
                    filter(lambda x: x.batch_state == BatchState.SALE, batch_aggregates)
                )

    def get_sales_data(
        self, session: Session, limit: int, offset: int
    ) -> list[SaleRecord]:
        sale_repository = SaleRepository(session)
        return sale_repository.get_sales_data(limit, offset)
