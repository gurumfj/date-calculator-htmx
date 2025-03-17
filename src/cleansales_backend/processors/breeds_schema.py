from datetime import date, datetime
from typing import Any, override

import pandas as pd
from pydantic import (
    ConfigDict,
    Field,
    computed_field,
    field_validator,
    model_validator,
)
from sqlmodel import Field as SQLModelField
from sqlmodel import Session, select

from cleansales_backend.core.db_monitor import log_execution_time
from cleansales_backend.domain.models import BreedRecord

from .interface.breed_repository_protocol import BreedRepositoryProtocol
from .interface.processors_interface import (
    IBaseModel,
    IORMModel,
    IProcessor,
    IResponse,
    RecordEvent,
)


class BreedRecordBase(IBaseModel):
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
    sub_location: str | None = Field(None, description="分場", alias="分場")
    veterinarian: str | None = Field(None, description="獸醫名稱", alias="Dr.")
    is_completed: bool = Field(False, description="是否完成", alias="結場")

    # 記錄資料
    chicken_breed: str = Field(..., description="雞的種類", alias="雞種")
    breed_date: date = Field(..., description="入雛日期", alias="入雛日期")
    chick_count: tuple[int, int] | None = Field(
        None, description="入雛數量", alias="入雛數量"
    )
    total_chick_count: int | None = Field(
        None, description="入雛總量", alias="入雛數量.1"
    )
    supplier: str | None = Field(None, description="種雞場名稱", alias="種雞場")

    model_config = ConfigDict(populate_by_name=True, from_attributes=True)

    @model_validator(mode="before")
    @classmethod
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

    @field_validator("is_completed", mode="before")
    @classmethod
    def validate_is_completed(cls, value: Any) -> bool:
        try:
            if isinstance(value, str):
                return value.strip() == "結場"
            return bool(value)
        except Exception:
            return False  # 發生異常時返回 False

    @computed_field
    def breed_male(self) -> int:
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
    def breed_female(self) -> int:
        try:
            if self.chick_count:
                return self.chick_count[1]
            if self.chicken_breed == "閹雞":
                return 0
            return self.total_chick_count // 2 if self.total_chick_count else 0
        except Exception as e:
            # logger.error("計算母雞數量錯誤: %s", str(e))
            raise ValueError(f"計算母雞數量錯誤: {str(e)}")


class BreedRecordORM(IORMModel, table=True):
    """入雛記錄資料模型

    記錄每批雞隻的入雛基本資料，包含農場資訊、畜主資料及批次詳細資訊

    屬性說明:
    - farm_name: 養殖場名稱
    - address: 養殖場地址
    - farm_license: 養殖場牌照號碼
    - farmer_name: 畜主姓名
    - farmer_address: 畜主地址
    - batch_name: 批次編號
    - veterinarian: 負責獸醫
    - chicken_breed: 雞種
    - male: 公雞數量
    - female: 母雞數量
    - breed_date: 入雛日期
    - supplier: 種雞場供應商
    - sub_location: 子場位置
    - is_completed: 結案狀態
    """

    unique_id: str = SQLModelField(..., primary_key=True, description="內容比對唯一值")

    # 基本資料
    farm_name: str = Field(default=..., description="牧場名稱")
    address: str | None = Field(default=None, description="牧場地址")
    farm_license: str | None = Field(default=None, description="登記證號")

    # 畜主資料
    farmer_name: str | None = Field(default=None, description="畜主姓名")
    farmer_address: str | None = Field(default=None, description="畜主地址")

    # 批次資料
    batch_name: str | None = SQLModelField(default=None, description="場別", index=True)
    veterinarian: str | None = Field(default=None, description="獸醫名稱")
    chicken_breed: str = Field(default="", description="雞種")
    breed_male: int = Field(default=0, description="入雛公雞數量")
    breed_female: int = Field(default=0, description="入雛母雞數量")
    breed_date: date = Field(default=..., description="入雛日期")
    supplier: str | None = Field(default=None, description="種雞場供應商")
    sub_location: str | None = Field(default=None, description="子場位置")
    is_completed: bool = Field(default=False, description="結場狀態")


class BreedRecordResponse(IResponse):
    pass


class BreedRecordProcessor(
    IProcessor[BreedRecordORM, BreedRecordBase, BreedRecordResponse],
    BreedRepositoryProtocol,
):
    @override
    def set_response_schema(self) -> type[BreedRecordResponse]:
        return BreedRecordResponse

    @override
    def set_validator_schema(self) -> type[BreedRecordBase]:
        return BreedRecordBase

    @override
    def set_orm_schema(self) -> type[BreedRecordORM]:
        return BreedRecordORM

    @override
    def get_all(self, session: Session) -> list[BreedRecord]:
        stmt = select(self._orm_schema).where(
            self._orm_schema.event == RecordEvent.ADDED
        )
        result = session.exec(stmt).all()
        return [BreedRecordProcessor.orm_to_domain(orm) for orm in result]

    @override
    def get_by_batch_name(self, session: Session, batch_name: str) -> list[BreedRecord]:
        result = self._get_by_criteria(session, {"batch_name": (batch_name, "eq")})
        return [BreedRecordProcessor.orm_to_domain(orm) for orm in result]


    @staticmethod
    def orm_to_domain(orm: BreedRecordORM) -> BreedRecord:
        return BreedRecord(
            farm_name=orm.farm_name,
            address=orm.address,
            farm_license=orm.farm_license,
            farmer_name=orm.farmer_name,
            farmer_address=orm.farmer_address,
            batch_name=orm.batch_name,
            veterinarian=orm.veterinarian,
            chicken_breed=orm.chicken_breed,
            male=orm.breed_male,
            female=orm.breed_female,
            breed_date=datetime.combine(orm.breed_date, datetime.min.time()),
            supplier=orm.supplier,
            sub_location=orm.sub_location,
            is_completed="結場" if orm.is_completed else None,
        )
