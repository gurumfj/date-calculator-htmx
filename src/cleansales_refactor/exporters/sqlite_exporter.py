import hashlib
from dataclasses import asdict
from datetime import date, datetime

from sqlmodel import Field, Session, SQLModel, create_engine, select

from cleansales_refactor.models import ProcessingResult, SaleRecord
from cleansales_refactor.exporters import IExporter


class SaleRecordORM(SQLModel, table=True):
    """銷售記錄資料表模型"""

    id: str = Field(default=None, primary_key=True, index=True, unique=True)
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
            results: dict[str, SaleRecord] = {
                self.get_unique_key(record): record for record in result.processed_data
            }
            result_keys: set[str] = set(results.keys())
            orm_keys: set[str] = self.get_all_keys(session)
            result_keys_to_save: set[str] = result_keys - orm_keys
            for key in result_keys_to_save:
                self.save_record(results[key], session)
            orm_keys_to_delete: set[str] = orm_keys - result_keys
            for key in orm_keys_to_delete:
                self.delete_record(key, session)
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

    def get_unique_key(self, record: SaleRecord) -> str:
        """sha256 取得唯一鍵值 by 所有欄位"""
        # 將所有值轉換為字串，None 轉換為空字串
        values = [
            str(value) if value is not None else "" for value in asdict(record).values()
        ]
        key = "".join(values)
        return hashlib.sha256(key.encode()).hexdigest()[:10]

    def get_record_by_key(self, key: str, session: Session) -> SaleRecordORM | None:
        """取得銷售記錄 by 唯一鍵值"""
        return session.get(SaleRecordORM, key)

    def save_record(self, record: SaleRecord, session: Session) -> None:
        """保存銷售記錄"""
        record_orm = SaleRecordORM(**asdict(record))
        record_orm.id = self.get_unique_key(record)
        session.add(record_orm)

    def delete_record(self, key: str, session: Session) -> None:
        """刪除銷售記錄"""
        orm_record = session.get(SaleRecordORM, key)
        if orm_record:
            session.delete(orm_record)

    def get_all_keys(self, session: Session) -> set[str]:
        """取得所有鍵值"""
        return set(record.id for record in session.exec(select(SaleRecordORM)))
