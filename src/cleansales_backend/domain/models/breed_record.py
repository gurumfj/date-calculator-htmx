from dataclasses import dataclass
from datetime import date, datetime

from sqlmodel import Field, SQLModel

from .batch_state import BatchState


@dataclass(frozen=True)
class BreedRecord:
    """入雛記錄資料模型

    記錄每批雞隻的入雛基本資料，包含農場資訊、畜主資料及批次詳細資訊
    frozen=True 確保資料不可變性

    屬性說明:
    - farm_name: 養殖場名稱
    - address: 養殖場地址
    - farm_license: 養殖場牌照號碼
    - farmer_name: 畜主姓名
    - farmer_address: 畜主地址
    - batch_name: 批次編號
    - veterinarian: 負責獸醫
    - chicken_breed: 雞種
    - male: 公雞數量
    - female: 母雞數量
    - breed_date: 入雛日期
    - supplier: 種雞場供應商
    - sub_location: 子場位置
    - is_completed: 結案狀態
    """

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
        """取得批次當前狀態

        根據是否結場(is_completed)判斷批次狀態:
        - 若已結場，回傳 COMPLETED
        - 否則回傳 BREEDING
        """
        return (
            BatchState.COMPLETED if self.is_completed == "結場" else BatchState.BREEDING
        )


class BreedRecordBase(SQLModel):
    """入雛記錄資料模型

    記錄每批雞隻的入雛基本資料，包含農場資訊、畜主資料及批次詳細資訊
    frozen=True 確保資料不可變性

    屬性說明:
    - farm_name: 養殖場名稱
    - address: 養殖場地址
    - farm_license: 養殖場牌照號碼
    - farmer_name: 畜主姓名
    - farmer_address: 畜主地址
    - batch_name: 批次編號
    - veterinarian: 負責獸醫
    - chicken_breed: 雞種
    - male: 公雞數量
    - female: 母雞數量
    - breed_date: 入雛日期
    - supplier: 種雞場供應商
    - sub_location: 子場位置
    - is_completed: 結案狀態
    """

    # 基本資料
    farm_name: str = Field(default="")
    address: str | None = Field(default=None)
    farm_license: str | None = Field(default=None)

    # 畜主資料
    farmer_name: str | None = Field(default=None)
    farmer_address: str | None = Field(default=None)

    # 批次資料
    batch_name: str | None = Field(default=None)
    veterinarian: str | None = Field(default=None)
    chicken_breed: str = Field(default="")
    male: int = Field(default=0)
    female: int = Field(default=0)
    breed_date: date
    supplier: str | None = Field(default=None)
    sub_location: str | None = Field(default=None)
    is_completed: str | None = Field(default=None)

    @property
    def batch_state(self) -> BatchState:
        """取得批次當前狀態

        根據是否結場(is_completed)判斷批次狀態:
        - 若已結場，回傳 COMPLETED
        - 否則回傳 BREEDING
        """
        return (
            BatchState.COMPLETED if self.is_completed == "結場" else BatchState.BREEDING
        )
