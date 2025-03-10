from datetime import date, datetime

from sqlmodel import SQLModel

from cleansales_refactor.domain.models import BatchState


class BatchAggregateResponseModel(SQLModel):
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


class SalesRecordResponseModel(SQLModel):
    closed: str | None
    handler: str | None
    date: datetime
    location: str
    customer: str
    male_count: int
    female_count: int
    total_weight: float | None
    total_price: float | None
    male_price: float | None
    female_price: float | None
    unpaid: str | None
