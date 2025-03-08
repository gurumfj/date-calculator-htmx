from datetime import date

from pydantic import BaseModel

from cleansales_refactor import BatchState


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
    sales_male: int
    sales_female: int
    total_sales: int
    sales_percentage: float
