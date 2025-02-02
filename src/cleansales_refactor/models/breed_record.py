import hashlib
from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class BreedRecord:
    """入雛記錄資料模型"""

    # 基本資料
    farm_name: str | None
    address: str | None
    farm_license: str | None

    # 畜主資料
    farmer_name: str | None
    farmer_address: str | None

    # 批次資料
    batch_name: str | None
    veterinarian: str | None
    chicken_breed: str | None
    male: int | None
    female: int | None
    breed_date: datetime | None
    supplier: str | None
    sub_location: str | None
    is_completed: str | None

    @property
    def unique_id(self) -> str:
        """唯一識別碼"""
        values = [str(value) for value in self.__dict__.values() if value is not None]
        key = "".join(values)
        return hashlib.sha256(key.encode()).hexdigest()[:10]
