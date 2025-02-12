from datetime import date
from typing import List, Optional

from pydantic import BaseModel

from cleansales_refactor import BatchState


class BreedInfo(BaseModel):
    supplier: Optional[str]
    breed_date: date
    chicken_breed: str
    male: int
    female: int
    day_age: int
    week_age: str


class BatchGroupBreedResponseModel(BaseModel):
    batch_name: str
    farm_name: str
    address: Optional[str]
    farmer_name: Optional[str]
    total_male: int
    total_female: int
    veterinarian: Optional[str]
    is_completed: bool
    breeds_info: List[BreedInfo]


class BatchAggregateModel(BaseModel):
    batch_name: str
    farm_name: str
    address: str | None
    farmer_name: str | None
    total_male: int
    total_female: int
    veterinarian: str | None
    batch_state: BatchState
    breed_date: tuple[date, ...]
    supplier: tuple[str | None, ...]
    chicken_breed: tuple[str, ...]
    male: tuple[int, ...]
    female: tuple[int, ...]
    day_age: tuple[int, ...]
    week_age: tuple[str, ...]