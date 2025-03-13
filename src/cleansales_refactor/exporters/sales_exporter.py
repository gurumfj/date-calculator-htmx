import hashlib
from dataclasses import asdict
from typing import Optional, override

from sqlmodel import Field, Relationship

from ..domain.models import SaleRecord, SaleRecordBase
from .base_sqlite_exporter import BaseSQLiteExporter
from .orm_models import BaseEventSource, ORMModel, ProcessingEvent


class SaleRecordORM(ORMModel, SaleRecordBase, table=True):
    """銷售記錄資料表模型"""

    event_source_id: int | None = Field(default=None, foreign_key="saleseventsource.id")
    event_source: Optional["SalesEventSource"] = Relationship(back_populates="records")


class SalesEventSource(BaseEventSource[SaleRecordORM], table=True):
    """銷售事件來源資料表模型"""

    records: list[SaleRecordORM] = Relationship(back_populates="event_source")


class SaleSQLiteExporter(
    BaseSQLiteExporter[SaleRecord, SaleRecordORM, SalesEventSource]
):
    """銷售記錄匯出服務 (使用 SQLite)"""

    @override
    def get_unique_key(self, record: SaleRecord) -> str:
        # """取得記錄的唯一識別碼"""
        # values = [str(value) for value in asdict(record).values() if value is not None]
        # key = "".join(values)
        return hashlib.sha256(str(record).encode()).hexdigest()[:10]

    @override
    def _record_to_orm(self, record: SaleRecord) -> SaleRecordORM:
        """將銷售記錄轉換為資料表模型"""
        record_orm = SaleRecordORM(
            **asdict(record),
            event=ProcessingEvent.ADDED.value,  # 使用 .value 獲取字串值
            event_source_id=0,
        )
        record_orm.unique_id = self.get_unique_key(record)
        return record_orm

    @override
    def _get_orm_class(self) -> type[SaleRecordORM]:
        """取得 ORM 類別"""
        return SaleRecordORM

    @override
    def _get_event_source_class(self) -> type[SalesEventSource]:
        """取得事件來源類別"""
        return SalesEventSource

    @override
    def _get_primary_key_field(self) -> str:
        """取得主鍵欄位名稱"""
        return "unique_id"
