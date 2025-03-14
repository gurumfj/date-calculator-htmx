import hashlib
from typing import TypeVar, override

from sqlmodel import Field, Relationship
from typing_extensions import Optional

from cleansales_backend.domain.models.breed_record import BreedRecordBase

from .base_sqlite_exporter import BaseSQLiteExporter
from .orm_models import BaseEventSource, ORMModel, ProcessingEvent

T = TypeVar("T")


class BreedRecordORM(ORMModel, BreedRecordBase, table=True):
    """入雛記錄資料表模型"""

    event_source_id: int | None = Field(foreign_key="breedeventsource.id")
    event_source: Optional["BreedEventSource"] = Relationship(back_populates="records")


class BreedEventSource(BaseEventSource[BreedRecordORM], table=True):
    """入雛事件來源資料表模型"""

    records: list[BreedRecordORM] = Relationship(back_populates="event_source")


class BreedSQLiteExporter(
    BaseSQLiteExporter[BreedRecordBase, BreedRecordORM, BreedEventSource]
):
    """入雛記錄匯出服務 (使用 SQLite)"""

    @override
    def get_unique_key(self, record: BreedRecordBase) -> str:
        """取得記錄的唯一識別碼"""
        # values: list[str] = [
        #     str(value) for value in record.__dict__.values() if value is not None
        # ]
        # key = "".join(values)
        return hashlib.sha256(str(record).encode()).hexdigest()[:10]

    @override
    def _record_to_orm(self, record: BreedRecordBase) -> BreedRecordORM:
        """將入雛記錄轉換為資料表模型"""
        # 創建 ORM 實例，使用枚舉的字串值
        record_orm = BreedRecordORM(
            **record.model_dump(),
            event=ProcessingEvent.ADDED.value,  # 使用 .value 獲取字串值
            unique_id=self.get_unique_key(record),
        )
        return record_orm

    @override
    def _get_event_source_class(self) -> type[BreedEventSource]:
        """取得事件來源類別"""
        return BreedEventSource

    @override
    def _get_orm_class(self) -> type[BreedRecordORM]:
        """取得 ORM 類別"""
        return BreedRecordORM

    @override
    def _get_primary_key_field(self) -> str:
        """取得主鍵欄位名稱"""
        return "unique_id"

    # @override
    # def _orm_to_record(self, orm: BreedRecordORM) -> BreedRecordBase:
    #     """將資料表模型轉換為入雛記錄"""
    #     return BreedRecordBase.model_validate(orm)
