from datetime import date, datetime
from typing import Any, override

import pandas as pd
from pydantic import (
    ConfigDict,
    Field,
)
from pydantic.functional_validators import field_validator, model_validator
from sqlmodel import Field as SQLModelField
from sqlmodel import Session

from cleansales_backend.domain.models.feed_record import FeedRecord
from cleansales_backend.processors.interface.feed_repository_protocol import (
    FeedRepositoryProtocol,
)

from .interface.processors_interface import (
    IBaseModel,
    IORMModel,
    IProcessor,
    IResponse,
)


class FeedRecordValidator(IBaseModel):
    # 必填資料
    batch_name: str = Field(..., description="場別", alias="場別")
    feed_date: datetime = Field(..., description="叫料日期", alias="日期")
    feed_manufacturer: str = Field(..., description="飼料廠", alias="飼料廠")
    feed_item: str = Field(..., description="品項", alias="品項")

    # 批次資料
    sub_location: str | None = Field(None, description="分場", alias="分場")
    is_completed: bool = Field(..., description="是否完成", alias="結場")

    # 記錄資料
    feed_week: str | None = Field(None, description="周齡", alias="周齡")
    feed_additive: str | None = Field(None, description="加藥", alias="加藥")
    feed_remark: str | None = Field(None, description="備註", alias="備註")

    model_config = ConfigDict(populate_by_name=True, from_attributes=True)

    # pd.nan to None
    @model_validator(mode="before")
    @classmethod
    def pdna_to_none(cls, values: dict[str, Any]) -> dict[str, Any]:
        try:
            # 必填欄位列表
            required_fields = ["場別", "日期", "飼料廠", "品項"]

            for key, value in values.items():
                # 處理 pd.NA 和 None
                if pd.isna(value):
                    # 如果是必填欄位但值為空，保留原值以便後續驗證報錯
                    if key in required_fields:
                        continue
                    values[key] = None
                    continue

                # 處理字串值
                if isinstance(value, str):
                    # 清除空白字符
                    cleaned_value = value.replace(" ", "")
                    # 如果清除空白後為空字串，且不是必填欄位，則設為 None
                    if cleaned_value == "":
                        if key in required_fields:
                            continue
                        values[key] = None
                    else:
                        values[key] = cleaned_value

                # 處理周齡欄位 - 確保數值型別能正確轉換為字串
                if key == "周齡" and value is not None:
                    values[key] = str(value)

            return values
        except Exception as e:
            # logger.error("轉換 pd.NA 錯誤: %s", str(e))
            raise ValueError(f"轉換 pd.NA 錯誤: {str(e)}")

    @field_validator("is_completed", mode="before")
    @classmethod
    def validate_is_completed(cls, value: Any) -> bool:
        try:
            if isinstance(value, str):
                return value.strip() == "結場"
            return False
        except Exception:
            return False  # 發生異常時返回 False


class FeedRecordORM(IORMModel, table=True):
    """飼料記錄資料模型"""

    unique_id: str = SQLModelField(..., primary_key=True, description="內容比對唯一值")

    # 必填資料
    batch_name: str = SQLModelField(default=..., description="場別", index=True)
    feed_date: date = Field(..., description="叫料日期")
    feed_manufacturer: str = Field(..., description="飼料廠")
    feed_item: str = Field(..., description="品項")

    # 批次資料
    sub_location: str | None = Field(None, description="分場")
    is_completed: bool = Field(..., description="是否完成")

    # 記錄資料
    feed_week: str | None = Field(None, description="周齡")
    feed_additive: str | None = Field(None, description="加藥")
    feed_remark: str | None = Field(None, description="備註")


class FeedRecordResponse(IResponse):
    pass


class FeedRecordProcessor(
    IProcessor[FeedRecordORM, FeedRecordValidator],
    FeedRepositoryProtocol,
):
    @override
    def set_processor_name(self) -> str:
        return "飼料"

    @override
    def set_validator_schema(self) -> type[FeedRecordValidator]:
        return FeedRecordValidator

    @override
    def set_orm_schema(self) -> type[FeedRecordORM]:
        return FeedRecordORM

    @override
    def set_orm_foreign_key(self) -> str:
        return "batch_name"

    @override
    def set_orm_date_field(self) -> str:
        return "feed_date"

    @override
    def get_by_batch_name(self, session: Session, batch_name: str) -> list[FeedRecord]:
        result = self._get_by_criteria(session, {"batch_name": (batch_name, "eq")})
        return [FeedRecordProcessor.orm_to_domain(orm) for orm in result]

    @staticmethod
    def orm_to_domain(orm: FeedRecordORM) -> FeedRecord:
        return FeedRecord.model_validate(orm)
