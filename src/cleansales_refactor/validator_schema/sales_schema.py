import logging
import re
from datetime import datetime
from typing import Any

import pandas as pd
from pydantic import ConfigDict, Field, field_validator, BaseModel


logger = logging.getLogger(__name__)


class SaleRecordValidatorSchema(BaseModel):
    """
    for sales data from excel validate
    """

    closed: str | None = Field(None, description="結案狀態", alias="結案")
    handler: str | None = Field(None, description="會磅狀態", alias="會磅")
    date: datetime = Field(..., description="銷售日期", alias="日期")
    location: str = Field(..., description="場別", alias="場別")
    customer: str = Field(..., description="客戶名稱", alias="客戶名稱")
    male_count: int = Field(..., description="公豬數量", alias="公-隻數")
    female_count: int = Field(..., description="母豬數量", alias="母-隻數")
    total_weight: float | None = Field(None, description="總重量", alias="總重\n(台斤)")
    total_price: float | None = Field(None, description="總價格", alias="總價")
    male_price: float | None = Field(None, alias="公-單價", description="公雞單價")
    female_price: float | None = Field(None, alias="母-單價", description="母雞單價")
    unpaid: str | None = Field(None, description="未付款狀態", alias="未收")

    @field_validator("date", mode="before")
    @classmethod
    def parse_date(cls, v: str | datetime) -> datetime:
        if isinstance(v, str):
            try:
                return datetime.strptime(v.strip(), "%Y-%m-%d")
            except ValueError:
                raise ValueError("日期格式不正確")
        return v

    @field_validator("customer", mode="before")
    @classmethod
    def clean_customer_name(cls, v: str) -> str:
        try:
            if pd.isna(v):
                raise ValueError("客戶名稱為空")
            if v.strip() == "":
                raise ValueError("客戶名稱為空")
            return v.strip()
        except Exception as e:
            logger.error("轉換客戶名稱錯誤: %s", str(e))
            raise ValueError("客戶名稱包含非法字符")

    @field_validator("male_count", "female_count", mode="before")
    @classmethod
    def validate_and_convert_int_columns(cls, v: Any) -> int:
        if pd.isna(v) or v is None:
            return 0
        if isinstance(v, str):
            if "." in v or " " in v:
                return 0
        return int(v)

    @field_validator("total_weight", "male_price", "female_price", "total_price", mode="before")
    @classmethod
    def validate_and_convert_columns(cls, v: str | float | None) -> float | None:
        if isinstance(v, str):
            try:
                return float(v) if "." in v else int(v)
            except ValueError:
                return None
        return v

    @field_validator("closed", "handler", "customer", "unpaid", mode="before")
    @classmethod
    def transform_str_columns(cls, v: str | None) -> str | None:
        if pd.isna(v):
            return None
        stripped_value = str(v).replace(" ", "")
        return None if stripped_value == "" else stripped_value

    @field_validator("location", mode="before")
    @classmethod
    def parse_primary_key_columns(cls, v: str) -> str:
        # 使用正規表達式進行多重替換
        v = re.sub(r"--", "-", v)  # 將 "--" 替換為 "-"
        v = re.sub(r"\s+", "", v)  # 去除所有空格
        v = re.sub(r"-N", "", v)  # 移除 "-N"

        if v.strip() == "":
            raise ValueError("場別為空")
        return v

    model_config = ConfigDict(populate_by_name=True, from_attributes=True)
