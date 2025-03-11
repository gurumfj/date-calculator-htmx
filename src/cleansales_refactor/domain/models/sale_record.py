from dataclasses import dataclass
from datetime import datetime

from .batch_state import BatchState


@dataclass(frozen=True)
class SaleRecord:
    """銷售記錄資料模型

    記錄每筆銷售交易的詳細資訊，包含銷售數量、重量、價格等
    frozen=True 確保資料不可變性

    屬性說明:
    - closed: 結案狀態
    - handler: 經手人
    - date: 銷售日期
    - location: 銷售地點
    - customer: 客戶名稱
    - male_count: 公雞銷售數量
    - female_count: 母雞銷售數量
    - total_weight: 總重量
    - total_price: 總金額
    - male_price: 公雞單價
    - female_price: 母雞單價
    - unpaid: 未付款狀態
    """

    closed: str | None
    handler: str | None
    date: datetime
    location: str
    customer: str
    male_count: int
    female_count: int
    total_weight: float | None
    total_price: float | None
    male_price: float | None
    female_price: float | None
    unpaid: str | None

    def _base_weight(self) -> float:
        """計算基礎重量

        使用總重量減去公雞額外重量(每隻0.8)後平均
        用於計算公母雞的平均重量
        """
        return (self.total_weight - self.male_count * 0.8) / (
            self.male_count + self.female_count
        )

    @property
    def sale_state(self) -> BatchState:
        """取得銷售狀態

        根據是否結案(closed)判斷狀態:
        - 若已結案，回傳 COMPLETED
        - 否則回傳 SALE
        """
        return BatchState.COMPLETED if self.closed == "結案" else BatchState.SALE

    @property
    def male_avg_weight(self) -> float | None:
        """計算公雞平均重量

        基礎重量加上0.8kg(公雞額外重量)
        若無公雞或總重量，回傳 None
        """
        if self.male_count == 0 or self.total_weight is None:
            return None
        base = self._base_weight()
        return base + 0.8 if base > 0 else None

    @property
    def female_avg_weight(self) -> float | None:
        """計算母雞平均重量

        直接使用基礎重量
        若無母雞或總重量，回傳 None
        """
        if self.female_count == 0 or self.total_weight is None:
            return None
        base = self._base_weight()
        return base if base > 0 else None

    def __str__(self) -> str:
        msg = []
        for k, v in self.__dict__.items():
            msg.append(f"{k}: {v}")
        return "\n".join(msg)
