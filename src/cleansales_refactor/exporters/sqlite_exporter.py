from dataclasses import asdict
from datetime import date
from typing import List

from sqlmodel import Field, Session, SQLModel, create_engine

from cleansales_refactor.models.sale_record import ProcessingResult

from ..models import SaleRecord
from ..services import IExporter


class SaleRecordORM(SQLModel, table=True):
    """銷售記錄資料表模型"""

    id: int | None = Field(default=None, primary_key=True)
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


class ErrorRecord(SQLModel, table=True):
    """錯誤記錄資料表模型"""

    id: int | None = Field(default=None, primary_key=True)
    message: str
    data: str
    extra: str
    timestamp: str


class SQLiteExporter(IExporter[SaleRecord]):
    """SQLite 匯出服務 (使用 SQLModel)"""

    def __init__(self, db_path: str) -> None:
        self.db_path = db_path
        self._engine = create_engine(f"sqlite:///{db_path}", echo=False)
        self._init_database()

    def _init_database(self) -> None:
        """初始化資料庫表格"""
        SQLModel.metadata.create_all(self._engine)

    def export_data(self, result: ProcessingResult[SaleRecord]) -> None:
        """將處理結果匯出至 SQLite 資料庫"""
        if not result.processed_data:
            raise ValueError("No grouped data to export")

        with Session(self._engine) as session:
            for record in result.processed_data:
                sale_records: List[SaleRecordORM] = [SaleRecordORM(**asdict(record))]
                session.add_all(sale_records)
            session.commit()

    def export_errors(self, result: ProcessingResult[SaleRecord]) -> None:
        """將錯誤資料匯出至 SQLite 資料庫"""
        with Session(self._engine) as session:
            error_records = [
                ErrorRecord(
                    message=error.message,
                    data=str(error.data),
                    extra=str(error.extra),
                    timestamp=error.timestamp,
                )
                for error in result.errors
            ]
            session.add_all(error_records)
            session.commit()
