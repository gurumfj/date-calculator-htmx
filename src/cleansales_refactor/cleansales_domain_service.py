from collections import defaultdict

from .domain.models.breed_record import BreedRecord
from .domain.models.breeds_groupby_batch_entity import BreedsGroupByBatch


class CleanSalesDomainService:
    def group_by_batch(
        self, breed_records: list[BreedRecord]
    ) -> list[BreedsGroupByBatch]:
        dict_by_batch = defaultdict(list)
        for record in breed_records:
            dict_by_batch[record.batch_name].append(record)
        return sorted(
            [
                BreedsGroupByBatch.create_from_breed_records(records)
                for records in dict_by_batch.values()
            ],
            key=lambda x: x.breeds_info[0].breed_date,
        )
