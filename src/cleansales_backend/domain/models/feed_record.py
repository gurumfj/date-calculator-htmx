from datetime import datetime

from pydantic import BaseModel, computed_field
from pydantic.config import ConfigDict

from .batch_state import BatchState


class FeedRecord(BaseModel):
    """飼料記錄資料模型"""

    # 必填資料
    batch_name: str
    feed_date: datetime
    feed_manufacturer: str
    feed_item: str

    # 批次資料
    sub_location: str | None
    is_completed: bool

    # 記錄資料
    feed_week: str | None
    feed_additive: str | None
    feed_remark: str | None

    model_config = ConfigDict(from_attributes=True, frozen=True)

    @computed_field
    @property
    def batch_state(self) -> BatchState:
        """取得批次當前狀態

        根據是否結場(is_completed)判斷批次狀態:
        - 若已結場，回傳 COMPLETED
        - 否則回傳 BREEDING
        """
        return BatchState.COMPLETED if self.is_completed else BatchState.BREEDING
