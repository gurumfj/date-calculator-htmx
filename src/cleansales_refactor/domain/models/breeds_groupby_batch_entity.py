from dataclasses import dataclass
from datetime import date
from typing import List

from .breed_record import BreedRecord


@dataclass
class Breeds:
    breed_date: date
    supplier: str | None
    chicken_breed: str
    male: int
    female: int


@dataclass
class BreedsGroupByBatch:
    batch_name: str
    farm_name: str
    address: str | None
    farmer_name: str | None
    total_male: int
    total_female: int
    veterinarian: str | None
    is_completed: bool
    breeds_info: List[Breeds]

    @classmethod
    def create_from_breed_records(
        cls, breed_records: list[BreedRecord]
    ) -> "BreedsGroupByBatch":
        if not all([
            record.batch_name == breed_records[0].batch_name for record in breed_records
        ]):
            raise ValueError("All breed records must be from the same batch")
        return cls(
            batch_name=breed_records[0].batch_name or "未知批次",
            farm_name=breed_records[0].farm_name,
            address=breed_records[0].address,
            farmer_name=breed_records[0].farmer_name,
            total_male=sum(record.male for record in breed_records),
            total_female=sum(record.female for record in breed_records),
            is_completed=breed_records[0].is_completed == "結案",
            veterinarian=breed_records[0].veterinarian,
            breeds_info=[
                Breeds(
                    breed_date=record.breed_date,
                    supplier=record.supplier,
                    chicken_breed=record.chicken_breed,
                    male=record.male,
                    female=record.female,
                )
                for record in breed_records
            ],
        )
