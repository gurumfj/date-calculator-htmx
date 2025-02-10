from datetime import date
from typing import List, Optional

from pydantic import BaseModel


class BreedInfo(BaseModel):
    breed_date: date
    supplier: Optional[str]
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
