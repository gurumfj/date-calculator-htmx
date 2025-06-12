import uuid
from datetime import datetime
from typing import TypeVar

import wcwidth
from pydantic import BaseModel, ConfigDict, Field, computed_field
from typing_extensions import override

from cleansales_backend.domain.models.sales_summary import SalesSummary

from ..utils import day_age
from .batch_state import BatchState
from .breed_record import BreedRecord
from .feed_record import FeedRecord
from .production_record import ProductionRecord
from .sale_record import SaleRecord
from .sales_summary import SalesSummaryModel

_ = wcwidth.WIDE_EASTASIAN


T = TypeVar("T")


class BatchAggregate:
    """批次資料彙整類別
    TODO: breeds, sales, feeds 各至成立ResponseModel

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
    feeds: list[FeedRecord]
    production: list[ProductionRecord]
    _cached_time: datetime

    def __init__(
        self,
        breeds: list[BreedRecord] = [],
        sales: list[SaleRecord] = [],
        feeds: list[FeedRecord] = [],
        production: list[ProductionRecord] = [],
    ) -> None:
        self.breeds = breeds
        self.sales = sales
        self.feeds = feeds
        self.production = production
        self._cached_time = datetime.now()
        self.validate()

    def validate(self) -> None:
        batch_name = set([record.batch_name for record in self.breeds])
        if len(batch_name) > 1:
            raise ValueError("All breed records must be from the same batch")
        if len(self.sales) > 0:
            sale_batch_name = set([record.batch_name for record in self.sales])
            if len(sale_batch_name) > 1:
                raise ValueError("All sale records must be from the same batch")
            if sale_batch_name != batch_name:
                raise ValueError("Sale batch name must match breed batch name")
        if len(self.feeds) > 0:
            feed_batch_name = set([record.batch_name for record in self.feeds])
            if len(feed_batch_name) > 1:
                raise ValueError("All feed records must be from the same batch")
            if feed_batch_name != batch_name:
                raise ValueError("Feed batch name must match breed batch name")
        if len(self.production) > 0:
            production_batch_name = set(
                [record.batch_name for record in self.production]
            )
            if len(production_batch_name) > 1:
                raise ValueError("All production records must be from the same batch")
            if production_batch_name != batch_name:
                raise ValueError("Production batch name must match breed batch name")

    @property
    def cached_time(self) -> datetime:
        return self._cached_time

    @property
    def last_updated_at(self) -> datetime:
        return max(
            [breed.updated_at for breed in self.breeds]
            + [sale.updated_at for sale in self.sales]
            + [feed.updated_at for feed in self.feeds]
            + [production.updated_at for production in self.production]
        )

    @property
    def batch_name(self) -> str | None:
        return self.breeds[0].batch_name

    @property
    def uuid(self) -> str | None:
        # using batch_name calculate uuid
        if self.batch_name is None:
            return None
        # 返回原始的 UUID
        return str(uuid.uuid5(uuid.NAMESPACE_DNS, self.batch_name))

    @property
    def safe_id(self) -> str | None:
        # 生成一個安全的 ID，適合用於 CSS 選擇器
        if self.batch_name is None:
            return None
        # 使用簡單的字母前綴加數字格式，確保在 CSS 選擇器中完全安全
        # 使用批次名稱的哈希值，確保唯一性
        return f"batch_{abs(hash(self.batch_name)) % 10000000:07d}"

    @staticmethod
    def get_safe_id(batch_name: str) -> str:
        # 生成一個安全的 ID，適合用於 CSS 選擇器
        # 使用簡單的字母前綴加數字格式，確保在 CSS 選擇器中完全安全
        # 使用批次名稱的哈希值，確保唯一性
        return f"batch_{abs(hash(batch_name)) % 10000000:07d}"

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
    def veterinarian(self) -> str | None:
        return self.breeds[0].veterinarian

    @property
    def batch_state(self) -> BatchState:
        # 如果所有飼養紀錄都已結案，則整個批次結案
        if all(b.batch_state == BatchState.COMPLETED for b in self.breeds):
            return BatchState.COMPLETED

        # 如果有銷售紀錄，則批次狀態為銷售中
        if self.sales and any(
            sale.sale_state == BatchState.SALE for sale in self.sales
        ):
            return BatchState.SALE

        # 預設狀態為養殖中
        return BatchState.BREEDING

    @property
    def sales_percentage(self) -> float | None:
        return self.sales_summary.sales_percentage if self.sales_summary else None

    @property
    def cycle_date(self) -> tuple[datetime, datetime | None]:
        min_date = min(breed.breed_date for breed in self.breeds)
        # 將 sale_date 從 datetime 轉換為 date 類型
        if self.sales:
            max_date = max(sale.sale_date for sale in self.sales)
        else:
            max_date = None
        return (min_date, max_date)

    @property
    def feed_manufacturer(self) -> set[str | None]:
        return set(feed.feed_manufacturer for feed in self.feeds)

    @property
    def sales_summary(self) -> SalesSummary | None:
        if not self.sales:
            return None
        return SalesSummary(self.sales, self.breeds)

    @property
    def batch_records(self) -> list["BatchRecordModel"]:
        return [BatchRecordModel.model_validate(breed) for breed in self.breeds]

    @override
    def __str__(self) -> str:
        """批次彙整資料"""
        result: list[str] = []
        result.append(f"批次: {self.batch_name}")
        result.append(f"飼養戶: {self.farmer_name}")
        result.append(f"場址: {self.address}")
        result.append(
            f"品種: {', '.join(set(breed.chicken_breed for breed in self.breeds))}"
        )
        result.append(f"入雛日期: {self.cycle_date[0].strftime('%Y-%m-%d')}")
        result.append(f"公雞數: {sum(breed.breed_male for breed in self.breeds):,} 隻")
        result.append(
            f"母雞數: {sum(breed.breed_female for breed in self.breeds):,} 隻"
        )
        result.append(f"獸醫師: {self.veterinarian}")
        result.append(
            f"種雞場: {', '.join(filter(None, set(breed.supplier for breed in self.breeds)))}"
        )
        result.append(f"批次狀態: {self.batch_state.value}")
        return "\n".join(result)

    def to_model(self) -> "BatchAggregateModel":
        """將 BatchAggregate 轉換為 BatchAggregateModel
        TODO: 改成轉換responseModel, Args可切換responseModel

        Args:
            batch: BatchAggregate 實例

        Returns:
            BatchAggregateModel: 對應的 BaseModel 實例
        """
        return BatchAggregateModel(
            updated_at=self.last_updated_at,
            batch_name=self.batch_name,
            farm_name=self.farm_name,
            address=self.address,
            farmer_name=self.farmer_name,
            veterinarian=self.veterinarian,
            batch_state=self.batch_state,
            feed_manufacturer=list(self.feed_manufacturer),
            sales_summary=self.sales_summary.to_model() if self.sales_summary else None,
            batch_records=self.batch_records,
        )


class BatchRecordModel(BaseModel):
    breed_date: datetime
    breed_male: int
    breed_female: int
    supplier: str | None
    chicken_breed: str
    sub_location: str | None
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True, frozen=True)


class SaleRecordModel(BaseModel):
    breed_date: list[datetime]
    handler: str | None
    sale_date: datetime
    customer: str
    male_count: int
    female_count: int
    total_weight: float | None
    total_price: float | None
    male_price: float | None
    female_price: float | None
    unpaid: bool
    male_avg_weight: float | None
    female_avg_weight: float | None
    avg_price: float | None

    model_config = ConfigDict(from_attributes=True, frozen=True)

    @computed_field
    @property
    def day_age(self) -> list[int]:
        return [day_age(date, self.sale_date) for date in self.breed_date]

    # @computed_field
    # @property
    # def week_age(self) -> list[str]:
    #     return [week_age(age) for age in self.day_age]

    @classmethod
    def create_from(
        cls, data: SaleRecord, breeds: list[BreedRecord]
    ) -> "SaleRecordModel":
        return cls(
            breed_date=[breed.breed_date for breed in breeds],
            handler=data.handler,
            sale_date=data.sale_date,
            customer=data.customer,
            male_count=data.male_count,
            female_count=data.female_count,
            total_weight=data.total_weight,
            total_price=data.total_price,
            male_price=data.male_price,
            female_price=data.female_price,
            unpaid=data.unpaid,
            male_avg_weight=data.male_avg_weight,
            female_avg_weight=data.female_avg_weight,
            avg_price=data.avg_price,
        )


class BatchAggregateModel(BaseModel):
    """批次資料彙整模型

    BatchAggregate 的 Pydantic BaseModel 版本
    用於 API 響應和資料驗證
    """

    # metadata
    updated_at: datetime

    # 基本資訊
    batch_name: str | None = Field(default=None, description="批次名稱")
    farm_name: str = Field(default=..., description="飼養戶名稱")
    address: str | None = Field(default=None, description="場址")
    farmer_name: str | None = Field(default=None, description="飼養戶名稱")

    # 批次資訊
    veterinarian: str | None = Field(default=None, description="獸醫師")
    batch_state: BatchState = Field(default=BatchState.BREEDING, description="批次狀態")
    feed_manufacturer: list[str | None] = Field(
        default_factory=list, description="飼料製造商"
    )
    batch_records: list[BatchRecordModel] = Field(
        default_factory=list, description="批次記錄"
    )

    # 日期資訊
    cycle_date: tuple[datetime, datetime | None] = Field(
        default=(datetime.min, None), description="周期日期"
    )

    # 資料統計
    sales_summary: SalesSummaryModel | None = Field(
        default=None, description="銷售統計"
    )

    model_config = ConfigDict(from_attributes=True, frozen=True)

    @classmethod
    def create_from(cls, data: BatchAggregate) -> "BatchAggregateModel":
        return cls(
            updated_at=data.last_updated_at,
            batch_name=data.batch_name,
            farm_name=data.farm_name,
            address=data.address,
            farmer_name=data.farmer_name,
            veterinarian=data.veterinarian,
            batch_state=data.batch_state,
            feed_manufacturer=list(data.feed_manufacturer),
            sales_summary=SalesSummaryModel.create_from(data.sales_summary)
            if data.sales_summary
            else None,
            cycle_date=data.cycle_date,
            batch_records=data.batch_records,
        )
