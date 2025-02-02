import hashlib
from dataclasses import asdict
from datetime import date, datetime

from sqlmodel import Field, SQLModel

from cleansales_refactor.exporters import BaseSQLiteExporter
from cleansales_refactor.models import SaleRecord


class SaleRecordORM(SQLModel, table=True):
    """銷售記錄資料表模型"""

    unique_id: str = Field(default=None, primary_key=True, index=True, unique=True)
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
    created_at: datetime = Field(default_factory=datetime.now)


# class ErrorRecord(SQLModel, table=True):
#     """錯誤記錄資料表模型"""

#     id: int | None = Field(default=None, primary_key=True)
#     message: str
#     data: str
#     extra: str
#     timestamp: str


class SaleSQLiteExporter(BaseSQLiteExporter[SaleRecord, SaleRecordORM]):
    """銷售記錄匯出服務 (使用 SQLite)"""

    def get_unique_key(self, record: SaleRecord) -> str:
        """取得記錄的唯一識別碼"""
        values = [
            str(value) if value is not None else "" for value in asdict(record).values()
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

    def _get_primary_key_field(self) -> str:
        """取得主鍵欄位名稱"""
        return "unique_id"
