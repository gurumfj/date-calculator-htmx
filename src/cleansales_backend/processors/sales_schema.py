import logging
import re
from datetime import date, datetime
from typing import Any, override

import pandas as pd
from pydantic import (
    ConfigDict,
    Field,
    computed_field,
    field_validator,
)
from sqlmodel import Field as SQLModelField
from sqlmodel import Session, and_, select

from cleansales_backend.domain.models import SaleRecord

from .interface.processors_interface import (
    IBaseModel,
    IORMModel,
    IProcessor,
    IResponse,
    RecordEvent,
)
from .interface.sale_repository_protocol import SaleRepositoryProtocol

# from sqlmodel import SQLModel

logger = logging.getLogger(__name__)


class SaleRecordValidator(IBaseModel):
    """銷售記錄驗證模式

    負責驗證和轉換銷售記錄的原始數據，確保數據的完整性和一致性。
    主要功能包括：
    1. 數據類型轉換（字符串轉數字等）
    2. 空值處理（None, NaN等）
    3. 數據清理（去除多餘空格、特殊字符等）
    4. 數據驗證（必填字段、格式檢查等）

    配置說明：
    - populate_by_name=True：允許按字段名稱填充
    - from_attributes=True：支持從對象屬性讀取
    """

    is_completed: bool = Field(False, description="結案狀態", alias="結案")
    handler: str | None = Field(None, description="會磅狀態", alias="會磅")
    sale_date: date = Field(..., description="銷售日期", alias="日期")
    batch_name: str = Field(description="場別", alias="場別")
    customer: str = Field(description="客戶名稱", alias="客戶名稱")
    male_count: int = Field(0, ge=0, description="公豬數量", alias="公-隻數")
    female_count: int = Field(0, ge=0, description="母豬數量", alias="母-隻數")
    total_weight: float | None = Field(None, description="總重量", alias="總重\n(台斤)")
    total_price: float | None = Field(None, description="總價格", alias="總價")
    male_price: float | None = Field(None, alias="公-單價", description="公雞單價")
    female_price: float | None = Field(None, alias="母-單價", description="母雞單價")
    b_unpaid: bool = Field(True, description="未付款狀態", alias="未收")
    b_paid: bool = Field(False, description="已付款狀態", alias="實收")

    model_config = ConfigDict(
        str_strip_whitespace=True,
        populate_by_name=True,
        from_attributes=True,
    )

    @field_validator("sale_date", mode="before")
    @classmethod
    def clean_sale_date(cls, v: Any) -> date | None:
        try:
            if pd.isna(v):
                return None
            if isinstance(v, (datetime, pd.Timestamp)):
                return v.date()
            return v
        except (ValueError, TypeError):
            logger.warning(f"無法將 {v} 轉換為日期，使用預設值 None")
            return None

    @field_validator("batch_name", mode="before")
    @classmethod
    def clean_batch_name(cls, v: Any) -> str | None:
        try:
            if pd.isna(v):
                return None
            if isinstance(v, str):
                v = re.sub(r"--", "-", v)  # 將 "--" 替換為 "-"
                v = re.sub(r"\s+", "", v)  # 去除所有空格
                v = re.sub(r"-N", "", v)  # 移除 "-N"
                return v.strip()
            return None
        except (ValueError, TypeError):
            logger.warning(f"無法將 {v} 轉換為字串，使用預設值 None")
            return None

    @field_validator("male_count", "female_count", mode="before")
    @classmethod
    def clean_count(cls, v: Any) -> int:
        try:
            if pd.isna(v):
                return 0
            return int(float(v))
        except (ValueError, TypeError):
            logger.warning(f"無法將 {v} 轉換為整數，使用預設值 None")
            return 0

    @field_validator("is_completed", mode="before")
    @classmethod
    def clean_is_completed(cls, v: Any) -> bool:
        try:
            if isinstance(v, str):
                return v.replace(" ", "").strip() == "結案"
            return False
        except (ValueError, TypeError):
            logger.warning(f"無法將 {v} 轉換為布林值，使用預設值 False")
            return False

    @field_validator("b_unpaid", mode="before")
    @classmethod
    def clean_unpaid(cls, v: Any) -> bool:
        try:
            if pd.isna(v):
                return False
            if isinstance(v, str):
                return v == "未付"
            return bool(v)
        except (ValueError, TypeError):
            logger.warning(f"無法將 {v} 轉換為布林值，使用預設值 False")
            return True

    @field_validator("b_paid", mode="before")
    @classmethod
    def clean_paid(cls, v: Any) -> bool:
        try:
            if pd.isna(v):
                return False
            if isinstance(v, str):
                return True
            return bool(v)
        except (ValueError, TypeError):
            logger.warning(f"無法將 {v} 轉換為布林值，使用預設值 False")
            return False

    @computed_field
    def unpaid(self) -> bool:
        return self.b_unpaid and not self.b_paid

    @field_validator("handler", mode="before")
    @classmethod
    def clean_handler(cls, v: Any) -> str | None:
        try:
            if pd.isna(v):
                return None
            return v
        except (ValueError, TypeError):
            logger.warning(f"無法將 {v} 轉換為字串，使用預設值 None")
            return None

    # all float field
    @field_validator(
        "male_price", "female_price", "total_price", "total_weight", mode="before"
    )
    @classmethod
    def clean_float(cls, v: Any) -> float | None:
        try:
            if pd.isna(v):
                return None
            return float(v)
        except (ValueError, TypeError):
            logger.warning(f"無法將 {v} 轉換為浮點數，使用預設值 None")
            return None


class SaleRecordORM(IORMModel, table=True):
    unique_id: str = SQLModelField(..., primary_key=True, description="內容比對唯一值")
    is_completed: bool = Field(False, description="結案狀態")
    handler: str | None = Field(None, description="會磅狀態")
    sale_date: date = Field(..., description="銷售日期")
    batch_name: str = SQLModelField(description="場別", index=True)
    customer: str = Field(description="客戶名稱")
    male_count: int = Field(0, ge=0, description="公豬數量")
    female_count: int = Field(0, ge=0, description="母豬數量")
    total_weight: float | None = Field(None, description="總重量")
    total_price: float | None = Field(None, description="總價格")
    male_price: float | None = Field(None, description="公雞單價")
    female_price: float | None = Field(None, description="母雞單價")
    unpaid: bool = Field(True, description="未付款狀態")


class SaleRecordResponse(IResponse):
    pass


class SaleRecordProcessor(
    IProcessor[SaleRecordORM, SaleRecordValidator],
    SaleRepositoryProtocol,
):
    @override
    def set_processor_name(self) -> str:
        return "販售"

    @override
    def set_validator_schema(self) -> type[SaleRecordValidator]:
        return SaleRecordValidator

    @override
    def set_orm_schema(self) -> type[SaleRecordORM]:
        return SaleRecordORM

    @override
    def set_orm_foreign_key(self) -> str:
        return "batch_name"

    @override
    def set_orm_date_field(self) -> str:
        return "sale_date"

    @override
    def get_sales_by_location(
        self, session: Session, location: str
    ) -> list[SaleRecord]:
        stmt = select(SaleRecordORM).where(
            and_(
                SaleRecordORM.batch_name == location,
                SaleRecordORM.event == RecordEvent.ADDED,
            )
        )
        sales_orm = session.exec(stmt).all()
        return [SaleRecordProcessor.orm_to_domain(orm) for orm in sales_orm]

    @override
    def get_sales_data(
        self, session: Session, limit: int = 300, offset: int = 0
    ) -> list[SaleRecord]:
        stmt = select(SaleRecordORM).limit(limit).offset(offset)
        sales_orm = session.exec(stmt).all()
        return [SaleRecordProcessor.orm_to_domain(orm) for orm in sales_orm]

    @staticmethod
    def orm_to_domain(orm: SaleRecordORM) -> SaleRecord:
        return SaleRecord.model_validate(orm)
