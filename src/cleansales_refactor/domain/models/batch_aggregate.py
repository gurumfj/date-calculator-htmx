from datetime import date, datetime

import pandas as pd

from .batch_state import BatchState
from .breed_record import BreedRecord
from .sale_record import SaleRecord


class SalesTrendData:
    """銷售走勢資料"""

    # TODO: 作為 BatchAggregate 的子屬性。
    def __init__(self, sales: list[SaleRecord], breeds: list[BreedRecord]) -> None:
        self.breeds = breeds
        self.sales = sales

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

    @property
    def total_revenue(self) -> float:
        """總營收"""
        return round(sum(sale.total_price or 0 for sale in self.sales), 2)

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
    def customer_statistics(self) -> dict[str, dict[str, float | int]]:
        """客戶統計"""
        from collections import defaultdict

        stats = defaultdict(lambda: {"交易次數": 0, "總金額": 0.0})
        for sale in self.sales:
            stats[sale.customer]["交易次數"] += 1
            stats[sale.customer]["總金額"] += sale.total_price or 0
            stats[sale.customer]["總金額"] = round(stats[sale.customer]["總金額"], 2)
        return dict(stats)

    @property
    def total_transactions(self) -> int:
        """總交易筆數"""
        return len(self.sales)

    def __str__(self) -> str:
        """銷售走勢資料"""
        # TODO: 最終目的 print(BatchAggregate.SalesTrendData) 時，會 print 銷售走勢資料
        msg = []
        msg.append(f"總交易筆數: {self.total_transactions}")
        msg.append(f"總營收: {self.total_revenue}")
        msg.append(f"平均公雞單價: {self.avg_male_price}")
        msg.append(f"平均母雞單價: {self.avg_female_price}")
        msg.append(f"銷售率: {round(self.sales_percentage * 100, 2)} %")
        msg.append(f"銷售數量: {self.total_sales:,} 隻")
        return "\n".join(msg)


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
    def sales_trend_data(self) -> SalesTrendData:
        return self._sales_trend_data

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
        return "\n".join(result)
