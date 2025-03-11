from dataclasses import dataclass
from datetime import datetime

from .batch_state import BatchState


@dataclass(frozen=True)
class BreedRecord:
    """入雛記錄資料模型"""

    # 基本資料
    farm_name: str
    address: str | None
    farm_license: str | None

    # 畜主資料
    farmer_name: str | None
    farmer_address: str | None

    # 批次資料
    batch_name: str | None
    veterinarian: str | None
    chicken_breed: str
    male: int
    female: int
    breed_date: datetime
    supplier: str | None
    sub_location: str | None
    is_completed: str | None

    @property
    def batch_state(self) -> BatchState:
        return (
            BatchState.COMPLETED if self.is_completed == "結場" else BatchState.BREEDING
        )
