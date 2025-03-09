from datetime import date, datetime
from enum import Enum

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

    def __str__(self) -> str:
        """批次彙整資料"""
        result = []
        result.append(f"批次編號: {self.batch_name}")
        result.append(f"飼養戶: {self.farmer_name}")
        result.append(f"場址: {self.address}")
        result.append(f"品種: {', '.join(self.chicken_breed)}")
        result.append(
            f"進雞日期: {', '.join(d.strftime('%Y-%m-%d') for d in self.breed_date)}"
        )
        result.append(f"日齡: {', '.join(str(d) for d in self.day_age)}")
        result.append(f"週齡: {', '.join(self.week_age)}")
        result.append(f"公雞數: {self.total_male:,} 隻 {self.male}")
        result.append(f"母雞數: {self.total_female:,} 隻 {self.female}")
        result.append(f"獸醫師: {self.veterinarian}")
        result.append(f"種雞場: {', '.join(filter(None, self.supplier))}")
        result.append(f"批次狀態: {self.batch_state.value}")
        result.append(
            f"銷售率: {self.sales_percentage * 100} %, 銷售數量: {self.total_sales:,} 隻"
        )
        result.append("-" * 80)
        return "\n".join(result)
