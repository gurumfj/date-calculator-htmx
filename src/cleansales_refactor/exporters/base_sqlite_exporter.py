import logging
from abc import ABC, abstractmethod
from typing import Generic, TypeVar

from sqlmodel import Field, Session, SQLModel, create_engine, select

from ..models import ProcessingResult
from .exporter_interface import IExporter

logger = logging.getLogger(__name__)

T = TypeVar("T")
M = TypeVar("M", bound=SQLModel)


class ErrorRecord(SQLModel, table=True):
    """基礎錯誤記錄資料表模型"""

    id: int | None = Field(default=None, primary_key=True)
    message: str
    data: str
    extra: str
    timestamp: str


class BaseSQLiteExporter(Generic[T, M], IExporter[T], ABC):
    """基礎 SQLite 匯出服務"""

    def __init__(self, db_path: str) -> None:
        self.db_path = db_path
        self._engine = create_engine(f"sqlite:///{db_path}", echo=False)
        self._init_database()

    def _init_database(self) -> None:
        """初始化資料庫表格"""
        SQLModel.metadata.create_all(self._engine)

    def export_data(self, data: ProcessingResult[T]) -> None:
        """匯出資料至 SQLite (實作 IExporter 介面)"""
        if not data.processed_data:
            raise ValueError("No data to export")

        with Session(self._engine) as session:
            try:
                all_existing_keys: set[str] = self._get_all_existing_keys(session)
                all_records_keys: set[str] = set(
                    self.get_unique_key(record) for record in data.processed_data
                )
                all_records_dict = {
                    self.get_unique_key(record): record
                    for record in data.processed_data
                }

                # 儲存新記錄
                keys_to_save = all_records_keys - all_existing_keys
                for key in keys_to_save:
                    self._save_data(session, all_records_dict[key])

                # 刪除不存在的記錄
                keys_to_delete = all_existing_keys - all_records_keys
                for key in keys_to_delete:
                    self._delete_data_by_key(session, key)

                session.commit()
                logger.info("資料匯出成功")
            except Exception as e:
                logger.error(f"匯出資料時發生錯誤: {e}")
                session.rollback()
                raise

    def export_errors(self, data: ProcessingResult[T]) -> None:
        """匯出錯誤記錄 (實作 IExporter 介面)"""
        with Session(self._engine) as session:
            error_records = [
                ErrorRecord(
                    message=error.message,
                    data=str(error.data),
                    extra=str(error.extra),
                    timestamp=error.timestamp,
                )
                for error in data.errors
            ]
            session.add_all(error_records)
            session.commit()

    def _save_data(self, session: Session, record: T) -> None:
        """儲存資料"""
        # print(f"儲存資料: {record}")
        logger.debug(f"儲存資料: {record}")
        orm_model = self._record_to_orm(record)
        session.add(orm_model)

    def _delete_data_by_key(self, session: Session, key: str) -> None:
        """刪除資料"""
        # print(f"刪除唯一識別碼: {key}")
        logger.debug(f"刪除唯一識別碼: {key}")
        model_to_delete = session.get(self._get_orm_class(), key)
        if model_to_delete:
            session.delete(model_to_delete)

    def _get_all_existing_keys(self, session: Session) -> set[str]:
        """取得所有已存在的唯一識別碼"""
        orm_class = self._get_orm_class()
        primary_key = self._get_primary_key_field()
        return set(session.exec(select(getattr(orm_class, primary_key))).all())

    @abstractmethod
    def get_unique_key(self, record: T) -> str:
        """取得記錄的唯一識別碼"""
        pass

    @abstractmethod
    def _record_to_orm(self, record: T) -> M:
        """將記錄轉換為 ORM 模型"""
        pass

    @abstractmethod
    def _get_orm_class(self) -> type[M]:
        """取得 ORM 類別"""
        pass

    @abstractmethod
    def _get_primary_key_field(self) -> str:
        """取得主鍵欄位名稱"""
        pass
