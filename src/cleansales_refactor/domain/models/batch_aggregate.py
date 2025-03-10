from datetime import date, datetime
from enum import Enum

import pandas as pd

from .breed_record import BreedRecord
from .sale_record import SaleRecord


class BatchState(Enum):
    BREEDING = "養殖中"
    SALE = "銷售中"
    COMPLETED = "結案"


class BatchAggregate:
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
    def batch_name(self) -> str:
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
        if self.sales and all(sale.closed == "結案" for sale in self.sales):
            return BatchState.COMPLETED

        # 如果有任何銷售紀錄，則處於銷售狀態
        if self.sales:
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
        day_age = lambda x: (datetime.now() - x).days + 1
        return tuple(day_age(breed.breed_date) for breed in self.breeds)

    @property
    def week_age(self) -> tuple[str, ...]:
        """週齡"""
        day = [7, 1, 2, 3, 4, 5, 6]
        day_age = lambda x: (datetime.now() - x).days + 1
        week_age = lambda x: f"{x // 7 - 1 if x % 7 == 0 else x // 7}/{day[x % 7]}"
        return tuple(week_age(day_age(breed.breed_date)) for breed in self.breeds)

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
    def sales_percentage(self) -> float:
        """銷售率"""
        if not self.sales:
            return 0

        total_breeds = sum(breed.male + breed.female for breed in self.breeds)
        return round(self.total_sales / total_breeds, 4)

    @property
    def sales_trend_data(self) -> dict[str, pd.DataFrame]:
        """使用 pandas 處理銷售走勢資料，供前端繪製走勢圖使用

        Returns:
            dict[str, pd.DataFrame]: {
                'daily': pd.DataFrame - 每日銷售資料
                'raw': pd.DataFrame - 原始銷售資料
            }
        """
        if not self.sales:
            return {"daily": pd.DataFrame(), "raw": pd.DataFrame()}

        # 直接將 sales records 轉換為 DataFrame
        df = pd.DataFrame(
            [
                {
                    "date": pd.to_datetime(sale.date),  # 確保轉換成 datetime
                    "customer": sale.customer,
                    "male_count": sale.male_count,
                    "female_count": sale.female_count,
                    "total_weight": sale.total_weight or 0,
                    "total_price": sale.total_price or 0,
                    "male_price": sale.male_price or 0,
                    "female_price": sale.female_price or 0,
                    "closed": sale.closed,
                }
                for sale in self.sales
            ]
        )

        if df.empty:
            return {"daily": pd.DataFrame(), "raw": pd.DataFrame()}

        # 計算每日統計資料
        daily_stats = (
            df.groupby("date")
            .agg(
                {
                    "male_count": "sum",
                    "female_count": "sum",
                    "total_weight": "sum",
                    "total_price": "sum",
                }
            )
            .round(2)
        )

        # 計算平均重量
        daily_stats["avg_weight"] = (
            daily_stats["total_weight"]
            / (daily_stats["male_count"] + daily_stats["female_count"])
        ).round(2)

        # 格式化日期
        daily_stats.index = daily_stats.index.strftime("%Y-%m-%d")

        return {
            "daily": daily_stats.to_dict(orient="index"),
            "raw": df.to_dict(orient="records"),
        }

    def __str__(self) -> str:
        """批次彙整資料"""
        result = []
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
        if self.sales:
            result.append(
                f"銷售率: {round(self.sales_percentage * 100, 2)} %, 銷售數量: {self.total_sales:,} 隻"
            )
        result.append("-" * 80)
        return "\n".join(result)
