from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class ProductionRecord(BaseModel):
    """批次生產成本記錄資料模型

    記錄每批雞隻的結案成本詳細數據，包括各項成本和費用的細項分析
    frozen=True 確保資料不可變性

    屬性說明:
    - id: 記錄唯一識別碼
    - batch_name: 批次名稱
    - feed_weight: 飼料重量
    - sale_weight_jin: 銷售重量(斤)
    - fcr: 飼料轉換率
    - meat_cost: 造肉成本
    - avg_price: 平均價格
    - cost_price: 成本價格
    - revenue: 收入
    - expenses: 總支出
    - feed_cost: 飼料成本
    - vet_cost: 獸醫成本
    - feed_med_cost: 飼料藥物成本
    - farm_med_cost: 農場藥物成本
    - leg_band_cost: 腳環成本
    - chick_cost: 雛雞成本
    - grow_fee: 飼養費用
    - catch_fee: 抓工費用
    - weigh_fee: 磅單費用
    - gas_cost: 瓦斯成本
    """

    # 基本資料
    id: int
    batch_name: str

    # 生產數據
    feed_weight: Decimal | None = None
    sale_weight_jin: Decimal | None = None
    fcr: Decimal | None = None
    avg_price: Decimal | None = None
    cost_price: Decimal | None = None
    revenue: Decimal | None = None

    # 成本項目
    expenses: Decimal
    meat_cost: Decimal | None = None
    feed_cost: Decimal | None = None
    vet_cost: Decimal | None = None
    feed_med_cost: Decimal | None = None
    farm_med_cost: Decimal | None = None
    leg_band_cost: Decimal | None = None
    chick_cost: Decimal | None = None
    grow_fee: Decimal | None = None
    catch_fee: Decimal | None = None
    weigh_fee: Decimal | None = None
    gas_cost: Decimal | None = None

    # metadata
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True, frozen=True)
