from datetime import datetime
from typing import override

from pydantic import BaseModel, ConfigDict


class SaleRecord(BaseModel):
    """銷售記錄資料模型

    記錄每筆銷售交易的詳細資訊，包含銷售數量、重量、價格等
    frozen=True 確保資料不可變性

    屬性說明:
    - is_completed: 結案狀態
    - handler: 經手人
    - sale_date: 銷售日期
    - batch_name: 批次名稱
    - customer: 客戶名稱
    - male_count: 公雞銷售數量
    - female_count: 母雞銷售數量
    - total_weight: 總重量
    - total_price: 總金額
    - avg_price: 平均單價
    - male_avg_weight: 公雞平均重量
    - female_avg_weight: 母雞平均重量
    - unpaid: 未付款狀態
    """

    is_completed: bool
    handler: str | None
    sale_date: datetime
    batch_name: str
    customer: str
    male_count: int
    female_count: int
    total_weight: float | None
    total_price: float | None
    male_price: float | None
    female_price: float | None
    unpaid: bool
    updated_at: datetime | None
    # Computed fields now provided by SQL
    sale_state: str | None = None
    avg_price: float | None = None
    male_avg_weight: float | None = None
    female_avg_weight: float | None = None

    model_config = ConfigDict(
        populate_by_name=True,
        from_attributes=True,
    )

    @override
    def __str__(self) -> str:
        msg: list[str] = []
        for k, v in self.__dict__.items():
            msg.append(f"{k}: {v}")
        return "\n".join(msg)
