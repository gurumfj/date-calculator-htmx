import logging
from datetime import datetime
from typing import Any

import pandas as pd
import wcwidth
from pydantic import BaseModel, Field, field_validator
from typing_extensions import TYPE_CHECKING

from ..utils import day_age
from .breed_record import BreedRecord
from .sale_record import SaleRecord

if TYPE_CHECKING:
    pass

_ = wcwidth.WIDE_EASTASIAN

logger = logging.getLogger(__name__)


class SalesDataModel(BaseModel):
    """銷售資料"""

    sale_date: datetime = Field(..., description="銷售日期")
    day_age: int = Field(..., description="日齡")
    customer: str = Field(..., description="客戶")
    male_count: int = Field(..., description="公雞數量")
    female_count: int = Field(..., description="母雞數量")
    total_weight: float | None = Field(..., description="總重量")
    male_avg_weight: float | None = Field(..., description="公雞平均重量")
    female_avg_weight: float | None = Field(..., description="母雞平均重量")
    avg_price: float | None = Field(..., description="平均單價")
    male_price: float | None = Field(..., description="公雞單價")
    female_price: float | None = Field(..., description="母雞單價")
    unpaid: str | None = Field(..., description="未付款")
    day_ages_detail: str = Field(..., description="日齡細節")

    @field_validator(
        "total_weight",
        "male_avg_weight",
        "female_avg_weight",
        "avg_price",
        "male_price",
        "female_price",
        mode="before",
    )
    @classmethod
    def clean_float(cls, v: Any) -> float | None:
        try:
            if pd.isna(v):
                return None
            return float(v)
        except (ValueError, TypeError):
            logger.warning(f"無法將 {v} 轉換為浮點數，使用預設值 None")
            return None


# DTO (Data Transfer Object) 用於 API 響應
class SalesPivotModel(BaseModel):
    """銷售走勢資料傳輸物件"""

    batch_name: str

    sales_data: list[SalesDataModel] = Field(
        ...,
        description="銷售資料列表，每個項目為一筆銷售記錄",
    )

    class Config:
        json_schema_extra: dict[str, Any] = {
            "example": {
                "sales_data": [
                    {
                        "sale_date": "2023-01-01",
                        "day_age": 35,
                        "customer": "客戶A",
                        "male_count": 50,
                        "female_count": 30,
                        "total_weight": 250.5,
                        "total_price": 25000.0,
                        "male_avg_weight": 2.8,
                        "female_avg_weight": 2.3,
                        "day_ages_detail": "35,42",
                    }
                ]
            }
        }


class SalesPivot:
    """銷售走勢資料"""

    _sales: list[SaleRecord]
    _breeds: list[BreedRecord]

    def __init__(self, sales: list[SaleRecord], breeds: list[BreedRecord]):
        self._sales = sales
        self._breeds = breeds

    @property
    def batch_name(self) -> str:
        return self._breeds[0].batch_name or self._breeds[0].farm_name

    @property
    def sales_data(self) -> pd.DataFrame:
        """銷售資料"""
        earliest_breed_date = min(breed.breed_date for breed in self._breeds)
        # 先創建基本的銷售資料 DataFrame
        base_data: list[dict[str, Any]] = [
            {
                "sale_date": sale.sale_date,
                "day_age": day_age(earliest_breed_date, sale.sale_date),
                "customer": sale.customer,
                "male_count": sale.male_count,
                "male_avg_weight": sale.male_avg_weight,
                "female_count": sale.female_count,
                "female_avg_weight": sale.female_avg_weight,
                "total_weight": sale.total_weight,
                "avg_price": sale.avg_price,
                "male_price": sale.male_price,
                "female_price": sale.female_price,
                "unpaid": sale.unpaid,
                "day_ages_detail": ",".join(
                    [
                        str(day_age(breed.breed_date, sale.sale_date))
                        for breed in self._breeds
                    ]
                ),
            }
            for sale in self._sales
        ]

        df = pd.DataFrame(base_data)
        # df = df.fillna(0)  # 將 NaN 值替換為 0

        return df

    def to_dto(self) -> SalesPivotModel:
        sales_data = [
            SalesDataModel.model_validate(row)
            for row in self.sales_data.to_dict(orient="records")
        ]

        return SalesPivotModel(
            batch_name=self.batch_name,
            sales_data=sales_data,
        )
