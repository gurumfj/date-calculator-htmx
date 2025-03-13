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

from pydantic import BaseModel, ConfigDict, Field

from cleansales_refactor.domain.models import BatchState


class BatchAggregateResponseModel(BaseModel):
    """批次聚合響應模型

    這個模型包含了批次的基本資訊、養殖資料以及銷售統計數據。
    主要分為三個部分：
    1. 基本資訊：批次名稱、場址、飼養戶等
    2. 養殖資料：入雛數量、日齡等
    3. 銷售統計：交易數量、營收、均重等
    """

    # 基本資訊
    batch_name: str | None = Field(
        None,
        description="批次名稱，用於識別特定的養殖批次",
    )

    farm_name: str = Field(
        ...,
        description="養殖場名稱",
    )

    address: str | None = Field(
        None,
        description="養殖場地址",
    )

    farmer_name: str | None = Field(
        None,
        description="飼養戶姓名",
    )

    veterinarian: str | None = Field(
        None,
        description="負責的獸醫師姓名",
    )

    batch_state: BatchState = Field(
        ...,
        description="批次狀態（養殖中、銷售中、已結案）",
    )

    # 養殖資料
    breed_date: tuple[date, ...] = Field(
        ...,
        description="入雛日期列表，可能有多個入雛批次",
    )

    supplier: tuple[str | None, ...] = Field(
        ...,
        description="種雞場列表，對應每個入雛批次",
    )

    chicken_breed: tuple[str, ...] = Field(
        ...,
        description="雞種列表，對應每個入雛批次",
    )

    male: tuple[int, ...] = Field(
        ...,
        description="各批次公雞數量",
    )

    female: tuple[int, ...] = Field(
        ...,
        description="各批次母雞數量",
    )

    total_male: int = Field(
        ...,
        description="飼養公雞總數量",
    )

    total_female: int = Field(
        ...,
        description="飼養母雞總數量",
    )

    day_age: tuple[int, ...] = Field(
        ...,
        description="各批次目前日齡",
    )

    week_age: tuple[str, ...] = Field(
        ...,
        description="各批次目前週齡，格式：週數/日數",
    )

    # 銷售統計
    total_transactions: int = Field(
        ...,
        description="總交易筆數",
    )

    sales_male: int = Field(
        ...,
        description="已售出公雞數量",
    )

    sales_female: int = Field(
        ...,
        description="已售出母雞數量",
    )

    total_sales: int = Field(
        ...,
        description="總銷售數量（公雞 + 母雞）",
    )

    sales_percentage: float = Field(
        ...,
        description="銷售率（已售出數量 / 總入雛數量）",
        ge=0,
        le=1,
    )

    total_revenue: float = Field(
        ...,
        description="總營收（新台幣）",
        ge=0,
    )

    avg_male_weight: float = Field(
        ...,
        description="平均公雞重量（台斤）",
        ge=0,
    )

    avg_female_weight: float = Field(
        ...,
        description="平均母雞重量（台斤）",
        ge=0,
    )

    avg_male_price: float = Field(
        ...,
        description="平均公雞單價（新台幣/台斤）",
        ge=0,
    )

    avg_female_price: float = Field(
        ...,
        description="平均母雞單價（新台幣/台斤）",
        ge=0,
    )

    # 銷售週期相關
    cycle_days: int = Field(
        ...,
        description="整個批次的循環天數",
        ge=0,
    )

    sales_duration: int = Field(
        ...,
        description="銷售期間的天數",
        ge=0,
    )

    sales_open_close_dayage: tuple[int, int] | None = Field(
        None,
        description="開場最大日齡和結案最小日齡",
    )

    cycle_date: tuple[date, date] | None = Field(
        None,
        description="批次循環起訖日期",
    )

    sales_period_date: tuple[date, date] | None = Field(
        None,
        description="銷售期間起訖日期",
    )

    avg_price_weight: float = Field(
        ...,
        description="平均單價（新台幣/台斤）",
        ge=0,
    )

    avg_weight: float = Field(
        ...,
        description="平均重量（台斤）",
        ge=0,
    )

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
