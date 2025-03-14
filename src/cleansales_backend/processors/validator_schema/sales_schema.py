import logging
import re
from datetime import date, datetime
from hashlib import sha256
from typing import Any

import pandas as pd
from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    computed_field,
    field_validator,
)

# from sqlmodel import Field, SQLModel
# from pydantic import BaseModel
from sqlmodel import Field as SQLModelField
from sqlmodel import SQLModel

# from sqlmodel import SQLModel

logger = logging.getLogger(__name__)


class SaleRecordBase(BaseModel):
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

    closed: bool = Field(False, description="結案狀態", alias="結案")
    handler: str | None = Field(None, description="會磅狀態", alias="會磅")
    sale_date: date = Field(..., description="銷售日期", alias="日期")
    location: str = Field(description="場別", alias="場別")
    customer: str = Field(description="客戶名稱", alias="客戶名稱")
    male_count: int = Field(0, ge=0, description="公豬數量", alias="公-隻數")
    female_count: int = Field(0, ge=0, description="母豬數量", alias="母-隻數")
    total_weight: float | None = Field(None, description="總重量", alias="總重\n(台斤)")
    total_price: float | None = Field(None, description="總價格", alias="總價")
    male_price: float | None = Field(None, alias="公-單價", description="公雞單價")
    female_price: float | None = Field(None, alias="母-單價", description="母雞單價")
    unpaid: bool = Field(True, description="未付款狀態", alias="未收")

    model_config = ConfigDict(
        str_strip_whitespace=True,
        populate_by_name=True,
        from_attributes=True,
    )

    @field_validator("sale_date", mode="before")
    @classmethod
    def clean_sale_date(cls, v: date | datetime) -> date:
        if isinstance(v, datetime):
            return v.date()
        return v

    @field_validator("location", mode="before")
    @classmethod
    def clean_location(cls, v: str) -> str:
        if "'" not in v:
            raise ValueError("場別中必須包含單引號")
        # 使用正規表達式進行多重替換
        v = re.sub(r"--", "-", v)  # 將 "--" 替換為 "-"
        v = re.sub(r"\s+", "", v)  # 去除所有空格
        v = re.sub(r"-N", "", v)  # 移除 "-N"
        return v.strip()

    @field_validator("male_count", "female_count", mode="before")
    @classmethod
    def clean_count(cls, v: Any) -> int:
        if pd.isna(v):
            return 0
        return int(v)

    @field_validator("closed", mode="before")
    @classmethod
    def clean_closed(cls, v: str) -> bool:
        return v == "結案"

    @field_validator("unpaid", mode="before")
    @classmethod
    def clean_unpaid(cls, v: str) -> bool:
        return v == "未付"

    @computed_field(description="內容比對唯一值", return_type=str)
    @property
    def unique_id(self) -> str:
        return sha256(self.model_dump_json(exclude={"unique_id"}).encode()).hexdigest()[
            :10
        ]


# class SaleRecordBase(SQLModel):


class SaleRecordORM(SQLModel, table=True):
    unique_id: str = SQLModelField(..., primary_key=True, description="內容比對唯一值")
    closed: bool = Field(False, description="結案狀態")
    handler: str | None = Field(None, description="會磅狀態")
    sale_date: date = Field(..., description="銷售日期")
    location: str = Field(description="場別")
    customer: str = Field(description="客戶名稱")
    male_count: int = Field(0, ge=0, description="公豬數量")
    female_count: int = Field(0, ge=0, description="母豬數量")
    total_weight: float | None = Field(None, description="總重量")
    total_price: float | None = Field(None, description="總價格")
    male_price: float | None = Field(None, description="公雞單價")
    female_price: float | None = Field(None, description="母雞單價")
    unpaid: bool = Field(True, description="未付款狀態")
    updated_at: datetime | None = Field(
        default_factory=datetime.now, description="更新時間", alias="更新時間"
    )


# class SaleRecordResponse(SaleRecordBase):
#     pass


class SaleRecordValidatorSchema(SaleRecordBase):
    pass
