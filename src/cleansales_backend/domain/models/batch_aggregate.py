from datetime import date, datetime

import pandas as pd
import wcwidth  # keep it for tabulate
from tabulate import tabulate

from .batch_state import BatchState
from .breed_record import BreedRecord
from .sale_record import SaleRecord

_ = wcwidth.WIDE_EASTASIAN


def format_currency(amount: float, round_to: int = 0) -> str:
    """格式化金額"""
    return f"NT$ {amount:,.{round_to}f}"


def day_age(
    breed_date: date | datetime,
    diff_date: date | datetime | pd.Timestamp = datetime.now().date(),
) -> int:
    """日齡計算函數

    計算從養殖日期到指定日期的天數差異

    Args:
        breed_date (date | datetime): 養殖開始日期
        diff_date (date | datetime | pd.Timestamp, optional):
            計算日齡的目標日期，默認為當前日期
            支持 pandas Timestamp 類型以兼容 DataFrame 操作

    Returns:
        int: 日齡天數（包含起始日，所以加1）
    """
    if isinstance(breed_date, datetime):
        breed_date = breed_date.date()
    # 增加對 pandas Timestamp 的支持
    if isinstance(diff_date, (datetime, pd.Timestamp)):
        diff_date = diff_date.date()
    return (diff_date - breed_date).days + 1


def week_age(day_age: int) -> str:
    """週齡"""
    day = [7, 1, 2, 3, 4, 5, 6]
    return (
        f"{day_age // 7 - 1 if day_age % 7 == 0 else day_age // 7}/{day[day_age % 7]}"
    )


class SalesTrendData:
    """銷售走勢資料類別

    整合並分析批次的銷售數據，提供各項統計指標
    包含銷售總量、營收、平均重量、客戶分析等

    主要功能:
    - 計算各項銷售統計指標
    - 產生銷售趨勢報表
    - 客戶交易分析
    """

    # TODO: 作為 BatchAggregate 的子屬性。
    def __init__(self, sales: list[SaleRecord], breeds: list[BreedRecord]) -> None:
        self.breeds = breeds
        self.sales = sales

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
    def sales_open_close_dayage(self) -> tuple[int, int] | None:
        """開場最大日齡, 結案最小日齡"""
        if not self.sales:
            return None
        earliest_breed_date = min(breed.breed_date for breed in self.breeds)
        latest_breed_date = max(breed.breed_date for breed in self.breeds)
        return (
            min(day_age(earliest_breed_date, sale.sale_date) for sale in self.sales),
            max(day_age(latest_breed_date, sale.sale_date) for sale in self.sales),
        )

    @property
    def cycle_date(self) -> tuple[date, date] | None:
        """循環日期"""
        if not self.sales:
            return None
        return (
            min(breed.breed_date for breed in self.breeds),
            max(sale.sale_date for sale in self.sales),
        )

    @property
    def cycle_days(self) -> int:
        """循環天數"""
        if not self.cycle_date:
            return 0
        return (self.cycle_date[1] - self.cycle_date[0]).days + 1

    @property
    def sales_period_date(self) -> tuple[datetime, datetime] | None:
        """銷售期間"""
        if not self.sales:
            return None
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

    """ DATA FRAME"""

    @property
    def sales_data(self) -> pd.DataFrame:
        """銷售資料"""
        # 先創建基本的銷售資料 DataFrame
        base_data: list[dict[str, datetime | str | int | float | None]] = [
            {
                "sale_date": sale.sale_date,
                "customer": sale.customer,
                "male_count": sale.male_count,
                "female_count": sale.female_count,
                "total_weight": sale.total_weight,
                "total_price": sale.total_price,
                "male_avg_weight": sale.male_avg_weight,
                "female_avg_weight": sale.female_avg_weight,
            }
            for sale in self.sales
        ]

        df = pd.DataFrame(base_data).sort_values("sale_date")

        # 取得最早的入雛日期
        earliest_breed_date = min(breed.breed_date for breed in self.breeds)

        # 主要日齡欄位（用於圖表）
        df["day_age"] = (
            df["sale_date"]
            .apply(
                lambda x: day_age(
                    breed_date=earliest_breed_date, diff_date=pd.Timestamp(x)
                )
            )
            .astype(int)
        )

        # 額外的詳細日齡資訊欄位
        df["day_ages_detail"] = df["sale_date"].apply(
            lambda x: [
                day_age(breed_date=breed.breed_date, diff_date=pd.Timestamp(x))
                for breed in self.breeds
            ]
        )

        return df

    @property
    def daily_pivot(self) -> pd.DataFrame:
        """日報表"""
        return self.sales_data.groupby("day_age").agg(
            {
                "male_count": "sum",
                "female_count": "sum",
                "total_weight": "sum",
                "total_price": "sum",
                "male_avg_weight": "mean",
                "female_avg_weight": "mean",
            }
        )

    @property
    def customer_statistics(self) -> pd.DataFrame:
        """客戶統計"""
        return (
            self.sales_data.groupby("customer")
            .agg(
                {
                    "sale_date": "count",
                    "male_count": "sum",
                    "female_count": "sum",
                    "total_weight": "sum",
                    "total_price": "sum",
                }
            )
            .sort_values("total_weight", ascending=False)
        ).reset_index()

    @property
    def total_transactions(self) -> int:
        """總交易筆數"""
        return len(self.sales)

    def __str__(self) -> str:
        """銷售走勢資料"""
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

        sales_table: str = tabulate(
            self.sales_data[
                [
                    "sale_date",
                    "day_age",
                    "customer",
                    "male_count",
                    "female_count",
                    "male_avg_weight",
                    "female_avg_weight",
                    "total_weight",
                    "total_price",
                ]
            ].values.tolist(),
            headers=[
                "日期",
                "日齡",
                "客戶",
                "公數",
                "母數",
                "公雞均重",
                "母雞均重",
                "總重量",
                "總金額",
            ],
            tablefmt="simple",
            stralign="left",
            numalign="decimal",
        )
        msg.append("銷售紀錄:")
        msg.append(sales_table)
        msg.append("日報表:")
        daily_table = tabulate(
            self.daily_pivot.values.tolist(),
            headers=[
                "日齡",
                "公數",
                "母數",
                "總重量",
                "總金額",
                "公雞均重",
                "母雞均重",
            ],
            tablefmt="simple",
            stralign="left",
            numalign="decimal",
        )
        msg.append(daily_table)
        msg.append("客戶統計:")
        customer_table = tabulate(
            self.customer_statistics.values.tolist(),
            headers=["客戶", "交易次數", "公數", "母數", "總重量", "總金額"],
            tablefmt="simple",
            stralign="left",
            numalign="decimal",
        )
        msg.append(customer_table)
        return "\n".join(msg)


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
    _sales_trend_data: SalesTrendData

    def __init__(
        self,
        breeds: list[BreedRecord] = [],
        sales: list[SaleRecord] = [],
    ) -> None:
        self.breeds = breeds
        self.sales = sales
        self._sales_trend_data = SalesTrendData(sales, breeds)
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
    def sales_trend_data(self) -> SalesTrendData:
        return self._sales_trend_data

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
