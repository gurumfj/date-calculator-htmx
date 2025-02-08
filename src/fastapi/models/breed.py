from datetime import date
from typing import List, Optional

from pydantic import BaseModel


class SubCardInfo(BaseModel):
    breed_date: date
    supplier: Optional[str]
    male: int
    female: int


class BreedCardModel(BaseModel):
    batch_name: str
    farm_name: Optional[str]
    address: Optional[str]
    farmer_name: Optional[str]
    chicken_breed: str
    total_male: int
    total_female: int
    veterinarian: Optional[str]
    is_completed: Optional[str]
    supplier: Optional[str]  # 只有單筆記錄時使用
    breed_date: Optional[date]  # 只有單筆記錄時使用
    sub_cards: List[SubCardInfo] = []  # 多筆記錄時使用


class BreedSectionModel(BaseModel):
    breed_type: str
    total_batches: int
    total_male: int
    total_female: int
    cards: List[BreedCardModel]


class BreedResponseModel(BaseModel):
    total_batches: int
    total_male: int
    total_female: int
    sections: List[BreedSectionModel]
