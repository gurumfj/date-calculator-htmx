from collections import defaultdict

from sqlmodel import Session

from cleansales_refactor.domain.models import BatchAggregate, BatchState, BreedRecord
from cleansales_refactor.repositories import BreedRepository, SaleRepository


class QueryService:
    def get_breeds_is_not_completed(self, session: Session) -> list[BatchAggregate]:
        breed_repository = BreedRepository(session)
        sale_repository = SaleRepository(session)
        batch_aggregates: list[BatchAggregate] = []
        breed_records_dict: dict[str, list[BreedRecord]] = defaultdict(list)
        breeds: list[BreedRecord] = breed_repository.get_not_completed_breeds()
        for breed in breeds:
            breed_records_dict[breed.batch_name].append(breed)

        for batch_name, breeds in breed_records_dict.items():
            sales = sale_repository.get_sales_by_location(batch_name)
            batch_aggregates.append(BatchAggregate(breeds=breeds, sales=sales))

        return list(
            filter(lambda x: x.batch_state != BatchState.COMPLETED, batch_aggregates)
        )
