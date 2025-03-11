"""
################################################################################
# API 數據模型模組
#
# 這個模組定義了所有 API 響應使用的數據模型，包括：
# - 批次聚合響應模型
# - 銷售記錄響應模型
# - 銷售統計響應模型
# - 銷售趨勢響應模型
#
# 主要功能：
# 1. 定義數據結構
# 2. 數據驗證規則
# 3. 序列化配置
################################################################################
"""

from datetime import date

from pydantic import BaseModel, ConfigDict

from cleansales_refactor.domain.models import BatchState


class BatchAggregateResponseModel(BaseModel):
    """批次聚合響應模型"""

    batch_name: str | None
    farm_name: str
    address: str | None
    farmer_name: str | None
    total_male: int
    total_female: int
    veterinarian: str | None
    batch_state: BatchState
    breed_date: tuple[date, ...]
    supplier: tuple[str, ...]
    chicken_breed: tuple[str, ...]
    male: tuple[int, ...]
    female: tuple[int, ...]
    day_age: tuple[int, ...]
    week_age: tuple[str, ...]
    sales_percentage: float
    model_config = ConfigDict(from_attributes=True)


# class SalesRecordResponseModel(BaseModel):
#     """銷售記錄響應模型"""

#     id: int
#     batch_name: str
#     customer_name: str
#     sale_date: datetime
#     quantity_male: int
#     quantity_female: int
#     price_male: float
#     price_female: float
#     total_amount: float
#     payment_status: str
#     payment_date: Optional[datetime]
#     notes: Optional[str]

#     model_config = ConfigDict(from_attributes=True)


# class SalesStatisticsResponseModel(BaseModel):
#     """銷售統計響應模型"""

#     total_sales: int
#     total_revenue: float
#     avg_price_male: float
#     avg_price_female: float
#     total_male: int
#     total_female: int
#     customer_statistics: Dict[str, Dict[str, float]]
#     location_statistics: Optional[Dict[str, Dict[str, float]]]
#     period_start: Optional[datetime]
#     period_end: Optional[datetime]

#     model_config = ConfigDict(from_attributes=True)


# class DailyTrendData(BaseModel):
#     """每日趨勢數據模型"""

#     date: date
#     total_sales: int
#     total_revenue: float
#     avg_price: float
#     male_count: int
#     female_count: int

#     model_config = ConfigDict(from_attributes=True)


# class SalesTrendResponseModel(BaseModel):
#     """銷售趨勢響應模型"""

#     daily_trends: List[DailyTrendData]
#     period_start: date
#     period_end: date
#     total_days: int

#     model_config = ConfigDict(from_attributes=True)
