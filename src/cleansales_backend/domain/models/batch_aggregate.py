from datetime import date
from typing import TypeVar

import wcwidth  # keep it for tabulate
from pydantic import BaseModel, ConfigDict, Field

from cleansales_backend.domain.models.sales_summary import SalesSummary

from ..utils import day_age, week_age
from .batch_state import BatchState
from .breed_record import BreedRecord
from .sale_record import SaleRecord
from .sales_summary import SalesSummaryModel

_ = wcwidth.WIDE_EASTASIAN


T = TypeVar("T")


class BatchAggregate:
    """批次資料彙整類別

    將入雛記錄(BreedRecord)和銷售記錄(SaleRecord)整合在一起
    提供完整的批次資訊查詢和管理功能

    主要功能:
    - 批次基本資訊管理
    - 驗證資料一致性
    - 計算批次狀態
    - 提供銷售趨勢分析
    """

    breeds: list[BreedRecord]
    sales: list[SaleRecord]

    def __init__(
        self,
        breeds: list[BreedRecord] = [],
        sales: list[SaleRecord] = [],
    ) -> None:
        self.breeds = breeds
        self.sales = sales
        self.validate()

    def validate(self) -> None:
        if not self.breeds:
            raise ValueError("Breed records are required")
        if not self.sales:
            return
        if not all(
            [record.batch_name == self.breeds[0].batch_name for record in self.breeds]
        ):
            raise ValueError("All breed records must be from the same batch")
        if not all(
            [record.location == self.breeds[0].batch_name for record in self.sales]
        ):
            raise ValueError("All sale records must be from the same location")
        if not self.breeds[0].batch_name == self.sales[0].location:
            raise ValueError("Breed batch name and sale location must be the same")

    @property
    def batch_name(self) -> str | None:
        return self.breeds[0].batch_name

    @property
    def farm_name(self) -> str:
        return self.breeds[0].farm_name

    @property
    def address(self) -> str | None:
        return self.breeds[0].address

    @property
    def farmer_name(self) -> str | None:
        return self.breeds[0].farmer_name

    @property
    def total_male(self) -> int:
        return sum(breed.male for breed in self.breeds)

    @property
    def total_female(self) -> int:
        return sum(breed.female for breed in self.breeds)

    @property
    def veterinarian(self) -> str | None:
        return self.breeds[0].veterinarian

    @property
    def batch_state(self) -> BatchState:
        # 如果所有銷售紀錄都已結案，則整個批次結案
        if all(b.batch_state == BatchState.COMPLETED for b in self.breeds):
            return BatchState.COMPLETED

        if self.sales and all(
            sale.sale_state == BatchState.COMPLETED for sale in self.sales
        ):
            return BatchState.COMPLETED

        if self.sales and any(
            sale.sale_state == BatchState.SALE for sale in self.sales
        ):
            return BatchState.SALE

        # 預設狀態為養殖中
        return BatchState.BREEDING

    @property
    def breed_date(self) -> tuple[date, ...]:
        return tuple(breed.breed_date for breed in self.breeds)

    @property
    def supplier(self) -> tuple[str | None, ...]:
        """種雞場"""
        return tuple(breed.supplier for breed in self.breeds)

    @property
    def chicken_breed(self) -> tuple[str, ...]:
        return tuple(breed.chicken_breed for breed in self.breeds)

    @property
    def male(self) -> tuple[int, ...]:
        return tuple(breed.male for breed in self.breeds)

    @property
    def female(self) -> tuple[int, ...]:
        return tuple(breed.female for breed in self.breeds)

    @property
    def day_age(self) -> tuple[int, ...]:
        """日齡"""
        return tuple(day_age(breed.breed_date) for breed in self.breeds)

    @property
    def week_age(self) -> tuple[str, ...]:
        """週齡"""
        return tuple(week_age(day_age(breed.breed_date)) for breed in self.breeds)

    @property
    def sales_percentage(self) -> float | None:
        return self.sales_summary.sales_percentage if self.sales_summary else None

    @property
    def sales_summary(self) -> SalesSummary | None:
        if not self.sales:
            return None
        return SalesSummary(self.sales, self.breeds)

    def __str__(self) -> str:
        """批次彙整資料"""
        result: list[str] = []
        result.append(f"批次: {self.batch_name}")
        result.append(f"飼養戶: {self.farmer_name}")
        result.append(f"場址: {self.address}")
        result.append(f"品種: {', '.join(self.chicken_breed)}")
        result.append(
            f"入雛日期: {', '.join(d.strftime('%Y-%m-%d') for d in self.breed_date)}"
        )
        result.append(f"日齡: {', '.join(str(d) for d in self.day_age)}")
        result.append(f"週齡: {', '.join(self.week_age)}")
        result.append(f"公雞數: {self.total_male:,} 隻 {self.male}")
        result.append(f"母雞數: {self.total_female:,} 隻 {self.female}")
        result.append(f"獸醫師: {self.veterinarian}")
        result.append(f"種雞場: {', '.join(filter(None, self.supplier))}")
        result.append(f"批次狀態: {self.batch_state.value}")
        return "\n".join(result)

    def to_model(self) -> "BatchAggregateModel":
        """將 BatchAggregate 轉換為 BatchAggregateModel

        Args:
            batch: BatchAggregate 實例

        Returns:
            BatchAggregateModel: 對應的 BaseModel 實例
        """
        return BatchAggregateModel(
            batch_name=self.batch_name,
            farm_name=self.farm_name,
            address=self.address,
            farmer_name=self.farmer_name,
            total_male=self.total_male,
            total_female=self.total_female,
            veterinarian=self.veterinarian,
            batch_state=self.batch_state,
            breed_date=list(self.breed_date),
            supplier=list(self.supplier),
            chicken_breed=list(self.chicken_breed),
            male=list(self.male),
            female=list(self.female),
            day_age=list(self.day_age),
            week_age=list(self.week_age),
            sales_summary=self.sales_summary.to_model() if self.sales_summary else None,
        )


class BatchAggregateModel(BaseModel):
    """批次資料彙整模型

    BatchAggregate 的 Pydantic BaseModel 版本
    用於 API 響應和資料驗證
    """

    # 基本資訊
    batch_name: str | None = Field(default=None, description="批次名稱")
    farm_name: str = Field(default=..., description="飼養戶名稱")
    address: str | None = Field(default=None, description="場址")
    farmer_name: str | None = Field(default=None, description="飼養戶名稱")

    # 數量統計
    total_male: int = Field(default=0, description="飼養公雞總數")
    total_female: int = Field(default=0, description="飼養母雞總數")

    # 批次資訊
    veterinarian: str | None = Field(default=None, description="獸醫師")
    batch_state: BatchState = Field(default=BatchState.BREEDING, description="批次狀態")

    # 列表資訊
    breed_date: list[date] = Field(
        default_factory=list, description="開始飼養（入雛）日期"
    )
    supplier: list[str | None] = Field(default_factory=list, description="種雞場")
    chicken_breed: list[str] = Field(default_factory=list, description="飼養品種")
    male: list[int] = Field(default_factory=list, description="飼養公雞數")
    female: list[int] = Field(default_factory=list, description="飼養母雞數")
    day_age: list[int] = Field(default_factory=list, description="目前日齡")
    week_age: list[str] = Field(default_factory=list, description="目前週齡")

    # 資料統計
    sales_summary: SalesSummaryModel | None = Field(
        default=None, description="銷售統計"
    )
    # sales_percentage: float | None = Field(default=None, description="銷售率")

    model_config = ConfigDict(from_attributes=True)

    @classmethod
    def create_from(cls, data: BatchAggregate) -> "BatchAggregateModel":
        return cls(
            batch_name=data.batch_name,
            farm_name=data.farm_name,
            address=data.address,
            farmer_name=data.farmer_name,
            total_male=data.total_male,
            total_female=data.total_female,
            veterinarian=data.veterinarian,
            batch_state=data.batch_state,
            breed_date=list(data.breed_date),
            supplier=list(data.supplier),
            chicken_breed=list(data.chicken_breed),
            male=list(data.male),
            female=list(data.female),
            day_age=list(data.day_age),
            week_age=list(data.week_age),
            sales_summary=SalesSummaryModel.create_from(data.sales_summary)
            if data.sales_summary
            else None,
        )
