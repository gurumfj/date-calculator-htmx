from datetime import date, datetime
from typing import override

from pydantic import BaseModel, ConfigDict

from ..utils import day_age, format_currency
from .breed_record import BreedRecord
from .sale_record import SaleRecord

# if TYPE_CHECKING:
from .sales_pivot import SalesPivot


class SalesSummary:
    """銷售走勢資料類別

    整合並分析批次的銷售數據，提供各項統計指標
    包含銷售總量、營收、平均重量、客戶分析等

    主要功能:
    - 計算各項銷售統計指標
    - 產生銷售趨勢報表
    - 客戶交易分析
    """

    breeds: list[BreedRecord]
    sales: list[SaleRecord]

    # TODO: 作為 BatchAggregate 的子屬性。
    def __init__(self, sales: list[SaleRecord], breeds: list[BreedRecord]) -> None:
        self.breeds = breeds
        self.sales = sales
        self.validate()

    def validate(self) -> None:
        if not self.sales or not self.breeds:
            raise ValueError("Sales and breeds must not be empty")

    """ SUMMARY """

    @property
    def sales_male(self) -> int:
        return sum(sale.male_count for sale in self.sales)

    @property
    def sales_female(self) -> int:
        return sum(sale.female_count for sale in self.sales)

    @property
    def total_sales(self) -> int:
        """總銷售數量"""
        return self.sales_male + self.sales_female

    @property
    def avg_weight(self) -> float:
        """平均重量"""
        if not any(sale.total_weight for sale in self.sales):
            return 0
        vaild_count = sum(
            sale.male_count + sale.female_count
            for sale in self.sales
            if sale.total_weight
        )
        return round(
            sum(sale.total_weight for sale in self.sales if sale.total_weight)
            / vaild_count,
            2,
        )

    @property
    def sales_open_close_dayage(self) -> tuple[int, int]:
        """開場最大日齡, 結案最小日齡"""
        earliest_breed_date = min(breed.breed_date for breed in self.breeds)
        latest_breed_date = max(breed.breed_date for breed in self.breeds)
        return (
            min(day_age(earliest_breed_date, sale.sale_date) for sale in self.sales),
            max(day_age(latest_breed_date, sale.sale_date) for sale in self.sales),
        )

    @property
    def cycle_date(self) -> tuple[date, date]:
        """循環日期"""
        return (
            min(breed.breed_date for breed in self.breeds),
            max(sale.sale_date for sale in self.sales),
        )

    @property
    def cycle_days(self) -> int:
        """循環天數"""
        return (self.cycle_date[1] - self.cycle_date[0]).days + 1

    @property
    def sales_period_date(self) -> tuple[datetime, datetime]:
        """銷售期間"""
        return (
            min(sale.sale_date for sale in self.sales),
            max(sale.sale_date for sale in self.sales),
        )

    @property
    def sales_duration(self) -> int:
        """銷售天數"""
        if not self.sales_period_date:
            return 0
        return (self.sales_period_date[1] - self.sales_period_date[0]).days + 1

    @property
    def sales_percentage(self) -> float:
        """銷售率"""
        if not self.sales:
            return 0

        total_breeds = sum(breed.male + breed.female for breed in self.breeds)
        return round(self.total_sales / total_breeds, 4)

    @property
    def total_revenue(self) -> float:
        """總營收"""
        return round(sum(sale.total_price or 0 for sale in self.sales), -3)

    @property
    def avg_male_weight(self) -> float:
        """平均公雞重量"""
        if not any(sale.male_avg_weight for sale in self.sales):
            return 0
        valid_weights = [
            sale.male_avg_weight for sale in self.sales if sale.male_avg_weight
        ]
        return round(sum(valid_weights) / len(valid_weights), 2)

    @property
    def avg_female_weight(self) -> float:
        """平均母雞重量"""
        if not any(sale.female_avg_weight for sale in self.sales):
            return 0
        valid_weights = [
            sale.female_avg_weight for sale in self.sales if sale.female_avg_weight
        ]
        return round(sum(valid_weights) / len(valid_weights), 2)

    @property
    def avg_male_price(self) -> float:
        """平均公雞單價"""
        if not any(sale.male_price for sale in self.sales):
            return 0
        valid_prices = [sale.male_price for sale in self.sales if sale.male_price]
        return round(sum(valid_prices) / len(valid_prices), 2)

    @property
    def avg_female_price(self) -> float:
        """平均母雞單價"""
        if not any(sale.female_price for sale in self.sales):
            return 0
        valid_prices = [sale.female_price for sale in self.sales if sale.female_price]
        return round(sum(valid_prices) / len(valid_prices), 2)

    @property
    def avg_price_weight(self) -> float:
        """平均單價"""
        if not any(sale.total_price for sale in self.sales):
            return 0
        if not any(sale.total_weight for sale in self.sales):
            return 0
        return round(
            sum(sale.total_price for sale in self.sales if sale.total_price)
            / sum(
                sale.total_weight
                for sale in self.sales
                if sale.total_weight and sale.total_price
            ),
            2,
        )

    @property
    def total_transactions(self) -> int:
        """總交易筆數"""
        return len(self.sales)

    @property
    def sales_pivot(self) -> SalesPivot:
        """銷售資料"""
        from .sales_pivot import SalesPivot

        return SalesPivot(self.sales, self.breeds)

    def to_model(self) -> "SalesSummaryModel":
        """將 SalesSummary 轉換為 SalesSummaryModel

        Returns:
            SalesSummaryModel: 對應的 BaseModel 實例
        """
        return SalesSummaryModel(
            sales_male=self.sales_male,
            sales_female=self.sales_female,
            total_sales=self.total_sales,
            total_transactions=self.total_transactions,
            avg_weight=self.avg_weight,
            sales_open_close_dayage=list(self.sales_open_close_dayage),
            cycle_date=list(self.cycle_date),
            cycle_days=self.cycle_days,
            sales_period_date=list(self.sales_period_date),
            sales_duration=self.sales_duration,
            sales_percentage=self.sales_percentage,
            total_revenue=self.total_revenue,
            avg_male_weight=self.avg_male_weight,
            avg_female_weight=self.avg_female_weight,
            avg_male_price=self.avg_male_price,
            avg_female_price=self.avg_female_price,
            avg_price_weight=self.avg_price_weight,
        )

    @override
    def __str__(self) -> str:
        """銷售資料"""
        msg: list[str] = []
        msg.append(f"總交易筆數: {self.total_transactions}")
        msg.append(f"總營收: {format_currency(self.total_revenue, 0)}")
        msg.append(f"平均重量: {self.avg_weight}")
        msg.append(f"平均公雞重量: {self.avg_male_weight}")
        msg.append(f"平均母雞重量: {self.avg_female_weight}")
        msg.append(f"平均公雞單價: {format_currency(self.avg_male_price, 2)}")
        msg.append(f"平均母雞單價: {format_currency(self.avg_female_price, 2)}")
        msg.append(f"平均單價: {format_currency(self.avg_price_weight, 2)}")
        msg.append(f"銷售率: {round(self.sales_percentage * 100, 2)} %")
        msg.append(f"銷售數量: {self.total_sales:,} 隻")
        msg.append(f"銷售天數: {self.sales_duration} 天")
        msg.append(f"循環天數: {self.cycle_days} 天")
        if self.sales_open_close_dayage:
            msg.append(f"開場最大日齡: {self.sales_open_close_dayage[0]}")
            msg.append(f"結案最小日齡: {self.sales_open_close_dayage[1]}")
        if self.cycle_date:
            msg.append(f"循環日期: {self.cycle_date[0]} ~ {self.cycle_date[1]}")
        if self.sales_period_date:
            msg.append(
                f"銷售期間: {self.sales_period_date[0]} ~ {self.sales_period_date[1]}"
            )
        return "\n".join(msg)


class SalesSummaryModel(BaseModel):
    """銷售走勢資料模型

    SalesSummary 的 Pydantic BaseModel 版本
    用於 API 響應和資料驗證
    """

    # 銷售數量統計
    sales_male: int
    sales_female: int
    total_sales: int
    total_transactions: int

    # 重量與價格
    avg_weight: float
    avg_male_weight: float
    avg_female_weight: float
    avg_male_price: float
    avg_female_price: float
    avg_price_weight: float

    # 銷售週期資訊
    sales_open_close_dayage: list[int]
    cycle_date: list[date]
    cycle_days: int
    sales_period_date: list[datetime]
    sales_duration: int

    # 銷售績效
    sales_percentage: float
    total_revenue: float

    model_config = ConfigDict(from_attributes=True)  # type: ignore

    @classmethod
    def create_from(cls, data: SalesSummary) -> "SalesSummaryModel":
        return cls(
            sales_male=data.sales_male,
            sales_female=data.sales_female,
            total_sales=data.total_sales,
            total_transactions=data.total_transactions,
            avg_weight=data.avg_weight,
            sales_open_close_dayage=list(data.sales_open_close_dayage),
            cycle_date=list(data.cycle_date),
            cycle_days=data.cycle_days,
            sales_period_date=list(data.sales_period_date),
            sales_duration=data.sales_duration,
            sales_percentage=data.sales_percentage,
            total_revenue=data.total_revenue,
            avg_male_weight=data.avg_male_weight,
            avg_female_weight=data.avg_female_weight,
            avg_male_price=data.avg_male_price,
            avg_female_price=data.avg_female_price,
            avg_price_weight=data.avg_price_weight,
        )
