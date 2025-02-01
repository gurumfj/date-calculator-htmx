from datetime import datetime
from typing import Optional

import pandas as pd
from pydantic import Field, model_validator, field_validator, computed_field
import logging

logger = logging.getLogger(__name__)

class BreedRecordValidatorSchema:
    """農場原始數據模型，用於驗證和轉換 Excel 數據。

    此模型處理從 Excel 匯入的原始數據，提供數據驗證和轉換功能。
    所有字段都是可選的，因為原始數據可能不完整。
    """

    # 基本資料
    farm_name: str = Field(..., description="牧場名稱", alias="畜牧場名")
    address: Optional[str] = Field(None, description="牧場地址", alias="畜牧場址")
    farm_license: Optional[str] = Field(None, description="登記證號", alias="登記證號")

    # 畜主資料
    farmer_name: str = Field(..., description="畜主姓名", alias="畜主姓名")
    farmer_address: Optional[str] = Field(
        None, description="畜主通訊地址", alias="畜主通訊地址"
    )

    # 批次資料
    o_batch_name: Optional[str] = Field(None, description="場別", alias="場別")
    batch_id: Optional[str] = Field(None, description="場別ID")
    sub_location: Optional[str] = Field(None, description="分場", alias="分場")
    veterinarian: str = Field("unknown", description="獸醫名稱", alias="Dr.")
    is_completed: bool = Field(False, description="是否完成", alias="結場")

    # 記錄資料
    chicken_breed: str = Field(..., description="雞的種類", alias="雞種")
    breed_date: datetime = Field(..., description="入雛日期", alias="入雛日期")
    o_record_chick_count: Optional[str] = Field(
        None, description="入雛數量", alias="入雛數量"
    )
    o_record_total_chick_count: int = Field(
        ..., description="入雛總量", alias="入雛數量.1"
    )
    supplier: str = Field(..., description="種雞場名稱", alias="種雞場")

    @model_validator(mode="before")
    def pdna_to_none(cls, values: dict) -> dict:
        """將 pd.NA 轉換為 None"""
        try:
            for key, value in values.items():
                if pd.isna(value):
                    values[key] = None
                if isinstance(value, str):
                    values[key] = value.replace(" ", "")
            return values
        except Exception as e:
            logger.error("轉換 pd.NA 錯誤: %s", str(e))
            raise

    @field_validator("veterinarian", mode="before")
    @classmethod
    def invalid_input_value_to_unknown(cls, value) -> str:
        try:
            if not isinstance(value, str):
                return "unknown"
            return value
        except Exception as e:
            logger.error("轉換場別錯誤: %s", str(e))
            raise

    @field_validator("breed_date", mode="before")
    @classmethod
    def validate_breed_date(cls, value) -> datetime:
        try:
            if isinstance(value, str):
                return datetime.strptime(value, "%Y/%m/%d")
            return value
        except Exception as e:
            logger.error("轉換入雛日期錯誤: %s", str(e))
            raise

    @field_validator("o_record_chick_count", mode="before")
    @classmethod
    def validate_chick_count(cls, value) -> Optional[str]:
        try:
            if isinstance(value, str):
                male, female = map(int, value.split("/"))
                return f"{male},{female}"
            return None
        except Exception as e:
            logger.error("轉換入雛數量錯誤: %s", str(e))
            raise

    @field_validator("o_record_total_chick_count", mode="before")
    @classmethod
    def validate_total_chick_count(cls, value) -> int:
        try:
            if isinstance(value, str):
                return int(value)
            return value
        except Exception as e:
            logger.error("轉換入雛總量錯誤: %s", str(e))
            raise

    @field_validator("is_completed", mode="before")
    @classmethod
    def validate_is_completed(cls, value) -> bool:
        try:
            if value is None:
                return False
            if isinstance(value, str):
                return value.strip() == "結場"
            return False
        except Exception as e:
            logger.error("轉換是否完成錯誤: %s", str(e))
            return False  # 發生異常時返回 False

    @computed_field
    @property
    def male(self) -> Optional[int]:
        try:
            if self.chicken_breed == "閹雞":
                return self.o_record_total_chick_count
            elif self.o_record_chick_count:
                male, _ = map(int, self.o_record_chick_count.split(","))
                return male
            elif self.o_record_total_chick_count > 0:
                return self.o_record_total_chick_count // 2

            return None
        except Exception as e:
            logger.error("計算公雞數量錯誤: %s", str(e))
            raise

    @computed_field
    @property
    def female(self) -> Optional[int]:
        try:
            if self.chicken_breed == "閹雞":
                return 0
            elif self.o_record_chick_count:
                _, female = map(int, self.o_record_chick_count.split(","))
                return female
            elif self.o_record_total_chick_count > 0:
                return self.o_record_total_chick_count // 2

            return None
        except Exception as e:
            logger.error("計算母雞數量錯誤: %s", str(e))
            raise

    @property
    def batch_name(self) -> Optional[str]:
        if self.batch_id:
            return self.batch_id
        else:
            return self.o_batch_name
