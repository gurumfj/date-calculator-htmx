"""
################################################################################
# Excel 銷售記錄模型模組
#
# 針對 Excel/Google Apps Script 友好格式的銷售記錄模型
#
# 特點：
# - 扁平化資料結構
# - 計算欄位預處理
# - 日期格式一致性
################################################################################
"""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from .. import utils
from .sale_record import SaleRecord


def format_date(date: datetime | None) -> str:
    """格式化日期為 ISO 字符串格式

    Args:
        date: 要格式化的日期

    Returns:
        格式化後的日期字符串，如果日期為 None 則返回空字符串
    """
    if date is None:
        return ""
    return date.isoformat()


class ExcelSaleRecord(BaseModel):
    """Excel格式銷售記錄模型

    用於 Excel/Google Apps Script 友好的銷售數據格式
    """

    # 批次信息
    batch_name: str = Field(default="", description="批次名稱")
    farm_name: str = Field(default="", description="養殖場名稱")
    breed_type: str = Field(default="", description="雞種類型")
    breed_date: str = Field(default="", description="養殖日期")

    # 銷售信息
    sale_date: str = Field(default="", description="銷售日期")
    day_age: str = Field(default="", description="日齡")
    week_age: str = Field(default="", description="週齡")
    handler: str = Field(default="", description="經手人")
    customer: str = Field(default="", description="客戶名稱")

    # 數量和重量
    male_count: int = Field(default=0, description="公雞數量")
    female_count: int = Field(default=0, description="母雞數量")
    total_count: int = Field(default=0, description="總數量")
    male_avg_weight: float | None = Field(default=None, description="公雞平均重量")
    female_avg_weight: float | None = Field(default=None, description="母雞平均重量")
    total_weight: float | None = Field(default=None, description="總重量")

    # 價格信息
    male_price: float | None = Field(default=None, description="公雞單價")
    female_price: float | None = Field(default=None, description="母雞單價")
    total_price: float | None = Field(default=None, description="總金額")
    avg_price: float | None = Field(default=None, description="平均單價")

    # 狀態信息
    status: str = Field(default="", description="狀態")
    unpaid: bool = Field(default=False, description="未付款狀態")

    # 更新信息
    updated_at: str = Field(default="", description="更新時間")

    model_config = ConfigDict(
        populate_by_name=True,
        from_attributes=True,
    )

    @staticmethod
    def create_from_sale_and_batch(
        sale: SaleRecord,
        batch_name: str,
        farm_name: str,
        breed_type: str,
        breed_date: datetime,
        day_age: list[int],
    ) -> "ExcelSaleRecord":
        """從銷售記錄和批次信息創建Excel格式的銷售記錄

        Args:
            sale: 原始銷售記錄
            batch_name: 批次名稱
            farm_name: 養殖場名稱
            breed_type: 雞種類型
            breed_date: 養殖日期
            day_age: 日齡

        Returns:
            Excel格式的銷售記錄
        """
        # 計算週齡
        week_age = [utils.week_age(day) for day in day_age]

        return ExcelSaleRecord(
            # 批次信息
            batch_name=batch_name,
            farm_name=farm_name,
            breed_type=breed_type,
            breed_date=format_date(breed_date),
            # 銷售信息
            sale_date=format_date(sale.sale_date),
            day_age=",".join(map(str, day_age)),
            week_age=",".join(map(str, week_age)),
            handler=sale.handler or "",
            customer=sale.customer,
            # 數量和重量
            male_count=sale.male_count,
            female_count=sale.female_count,
            total_count=sale.male_count + sale.female_count,
            male_avg_weight=sale.male_avg_weight,
            female_avg_weight=sale.female_avg_weight,
            total_weight=sale.total_weight,
            # 價格信息
            male_price=sale.male_price,
            female_price=sale.female_price,
            total_price=sale.total_price,
            avg_price=sale.avg_price,
            # 狀態信息
            status=sale.sale_state.name,
            unpaid=sale.unpaid,
            # 更新信息
            updated_at=format_date(sale.updated_at),
        )

    def to_dict(self) -> dict[str, Any]:
        """將模型轉換為字典

        Returns:
            模型的字典表示
        """
        return self.model_dump(mode="json")
