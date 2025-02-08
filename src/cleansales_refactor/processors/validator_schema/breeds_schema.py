from datetime import datetime
from typing import Any

import pandas as pd
from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    computed_field,
    field_validator,
    model_validator,
)


class BreedRecordValidatorSchema(BaseModel):
    """農場原始數據模型，用於驗證和轉換 Excel 數據。

    此模型處理從 Excel 匯入的原始數據，提供數據驗證和轉換功能。
    所有字段都是可選的，因為原始數據可能不完整。
    """

    # 基本資料
    farm_name: str = Field(..., description="牧場名稱", alias="畜牧場名")
    address: str | None = Field(None, description="牧場地址", alias="畜牧場址")
    farm_license: str | None = Field(None, description="登記證號", alias="登記證號")

    # 畜主資料
    farmer_name: str | None = Field(None, description="畜主姓名", alias="畜主姓名")
    farmer_address: str | None = Field(
        None, description="畜主通訊地址", alias="畜主通訊地址"
    )

    # 批次資料
    batch_name: str | None = Field(None, description="場別", alias="場別")
    # batch_id: Optional[str] = Field(None, description="場別ID")
    sub_location: str | None = Field(None, description="分場", alias="分場")
    veterinarian: str | None = Field(None, description="獸醫名稱", alias="Dr.")
    is_completed: str | None = Field(None, description="是否完成", alias="結場")

    # 記錄資料
    chicken_breed: str = Field(..., description="雞的種類", alias="雞種")
    breed_date: datetime = Field(..., description="入雛日期", alias="入雛日期")
    chick_count: tuple[int, int] | None = Field(
        None, description="入雛數量", alias="入雛數量"
    )
    total_chick_count: int | None = Field(
        None, description="入雛總量", alias="入雛數量.1"
    )
    supplier: str | None = Field(None, description="種雞場名稱", alias="種雞場")

    model_config = ConfigDict(populate_by_name=True, from_attributes=True)

    @model_validator(mode="before")
    def pdna_to_none(cls, values: dict[str, Any]) -> dict[str, Any]:
        """將 pd.NA 轉換為 None"""
        try:
            for key, value in values.items():
                if pd.isna(value):
                    values[key] = None
                if isinstance(value, str):
                    values[key] = (
                        None if value.replace(" ", "") == "" else value.replace(" ", "")
                    )
            return values
        except Exception as e:
            # logger.error("轉換 pd.NA 錯誤: %s", str(e))
            raise ValueError(f"轉換 pd.NA 錯誤: {str(e)}")

    @field_validator("veterinarian", mode="before")
    @classmethod
    def invalid_input_value_to_unknown(cls, value: Any) -> str:
        try:
            if not isinstance(value, str):
                return "unknown"
            return value
        except Exception as e:
            # logger.error("轉換場別錯誤: %s", str(e))
            raise ValueError(f"轉換場別錯誤: {str(e)}")

    # @field_validator("breed_date", mode="before")
    # @classmethod
    # def validate_breed_date(cls, value) -> datetime:
    #     try:
    #         if isinstance(value, str):
    #             return datetime.strptime(value, "%Y/%m/%d")
    #         return value
    #     except Exception as e:
    #         logger.error("轉換入雛日期錯誤: %s", str(e))
    #         raise

    @field_validator("chick_count", mode="before")
    @classmethod
    def validate_chick_count(cls, value: Any) -> tuple[int, int] | None:
        try:
            if isinstance(value, str):
                male, female = map(int, value.split("/"))
                return male, female
            return None
        except Exception as e:
            # logger.error("轉換入雛數量錯誤: %s", str(e))
            raise ValueError(f"轉換入雛數量錯誤: {str(e)}")

    @field_validator("total_chick_count", mode="before")
    @classmethod
    def validate_total_chick_count(cls, value: Any) -> int:
        try:
            if not isinstance(value, int):
                return int(value)
            return value or 0
        except Exception as e:
            # logger.error("轉換入雛總量錯誤: %s", str(e))
            raise ValueError(f"轉換入雛總量錯誤: {str(e)}")

    # @field_validator("is_completed", mode="before")
    # @classmethod
    # def validate_is_completed(cls, value) -> bool:
    #     try:
    #         if value is None:
    #             return False
    #         if isinstance(value, str):
    #             return value.strip() == "結場"
    #         return False
    #     except Exception as e:
    #         logger.error("轉換是否完成錯誤: %s", str(e))
    #         return False  # 發生異常時返回 False

    @computed_field
    def male(self) -> int:
        try:
            if self.chick_count:
                return self.chick_count[0]
            if self.chicken_breed == "閹雞":
                return self.total_chick_count or 0
            return self.total_chick_count // 2 if self.total_chick_count else 0
        except Exception as e:
            # logger.error("計算公雞數量錯誤: %s", str(e))
            raise ValueError(f"計算公雞數量錯誤: {str(e)}")

    @computed_field
    def female(self) -> int:
        try:
            if self.chick_count:
                return self.chick_count[1]
            if self.chicken_breed == "閹雞":
                return 0
            return self.total_chick_count // 2 if self.total_chick_count else 0
        except Exception as e:
            # logger.error("計算母雞數量錯誤: %s", str(e))
            raise ValueError(f"計算母雞數量錯誤: {str(e)}")
