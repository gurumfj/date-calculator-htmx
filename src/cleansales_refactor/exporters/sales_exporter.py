import hashlib
from dataclasses import asdict
from datetime import date
from typing import List, Optional

from sqlmodel import Field, Relationship

from cleansales_refactor.exporters import BaseSQLiteExporter
from cleansales_refactor.models import SaleRecord
from cleansales_refactor.models.orm_models import BaseEventSource, ORMModel


class SaleRecordORM(ORMModel, table=True):
    """銷售記錄資料表模型"""

    __tablename__ = "sale_record"

    closed: str | None
    handler: str | None
    date: date
    location: str
    customer: str
    male_count: int
    female_count: int
    total_weight: float | None
    total_price: float | None
    male_price: float | None
    female_price: float | None
    unpaid: str | None
    event_source_id: int = Field(foreign_key="sales_event_source.id")
    event_source: Optional["SalesEventSource"] = Relationship(back_populates="records")


class SalesEventSource(BaseEventSource[SaleRecordORM], table=True):
    """銷售事件來源資料表模型"""

    __tablename__ = "sales_event_source"
    records: List[SaleRecordORM] = Relationship(back_populates="event_source")


class SaleSQLiteExporter(
    BaseSQLiteExporter[SaleRecord, SaleRecordORM, SalesEventSource]
):
    """銷售記錄匯出服務 (使用 SQLite)"""

    def get_unique_key(self, record: SaleRecord) -> str:
        """取得記錄的唯一識別碼"""
        values = [
            str(value) for value in asdict(record).values() if value is not None
        ]
        key = "".join(values)
        return hashlib.sha256(key.encode()).hexdigest()[:10]

    def _record_to_orm(self, record: SaleRecord) -> SaleRecordORM:
        """將銷售記錄轉換為資料表模型"""
        record_orm = SaleRecordORM(**asdict(record))
        record_orm.unique_id = self.get_unique_key(record)
        return record_orm

    def _get_orm_class(self) -> type[SaleRecordORM]:
        """取得 ORM 類別"""
        return SaleRecordORM

    def _get_event_source_class(self) -> type[SalesEventSource]:
        """取得事件來源類別"""
        return SalesEventSource

    def _get_primary_key_field(self) -> str:
        """取得主鍵欄位名稱"""
        return "unique_id"
