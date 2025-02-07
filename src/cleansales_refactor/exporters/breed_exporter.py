import hashlib
from dataclasses import asdict
from datetime import datetime
from typing import Optional, TypeVar

from sqlmodel import Field, Relationship

from ..models import BreedRecord
from ..models.orm_models import BaseEventSource, ORMModel
from .base_sqlite_exporter import BaseSQLiteExporter

T = TypeVar("T")


class BreedRecordORM(ORMModel, table=True):
    """入雛記錄資料表模型"""

    __tablename__ = "breed_record"  # type: ignore
    unique_id: str = Field(default=None, primary_key=True, index=True, unique=True)

    # 基本資料
    farm_name: str | None
    address: str | None
    farm_license: str | None

    # 畜主資料
    farmer_name: str | None
    farmer_address: str | None

    # 批次資料
    batch_name: str | None
    veterinarian: str | None
    chicken_breed: str | None
    male: int | None
    female: int | None
    breed_date: datetime
    supplier: str | None
    sub_location: str | None
    is_completed: str | None
    event_source_id: int = Field(foreign_key="breed_event_source.id")
    event_source: Optional["BreedEventSource"] = Relationship(back_populates="records")


class BreedEventSource(BaseEventSource[BreedRecordORM], table=True):
    """入雛事件來源資料表模型"""

    __tablename__ = "breed_event_source"  # type: ignore
    records: list[BreedRecordORM] = Relationship(back_populates="event_source")


class BreedSQLiteExporter(
    BaseSQLiteExporter[BreedRecord, BreedRecordORM, BreedEventSource]
):
    """入雛記錄匯出服務 (使用 SQLite)"""

    def get_unique_key(self, record: BreedRecord) -> str:
        """取得記錄的唯一識別碼"""
        values = [str(value) for value in asdict(record).values() if value is not None]
        key = "".join(values)
        return hashlib.sha256(key.encode()).hexdigest()[:10]

    def _record_to_orm(self, record: BreedRecord) -> BreedRecordORM:
        """將入雛記錄轉換為資料表模型"""
        record_orm = BreedRecordORM(**asdict(record))
        record_orm.unique_id = self.get_unique_key(record)
        return record_orm
    
    def _get_event_source_class(self) -> type[BreedEventSource]:
        """取得事件來源類別"""
        return BreedEventSource

    def _get_orm_class(self) -> type[BreedRecordORM]:
        """取得 ORM 類別"""
        return BreedRecordORM

    def _get_primary_key_field(self) -> str:
        """取得主鍵欄位名稱"""
        return "unique_id"

    def _orm_to_record(self, orm: BreedRecordORM) -> BreedRecord:
        """將資料表模型轉換為入雛記錄"""
        return BreedRecord(**orm.__dict__)
