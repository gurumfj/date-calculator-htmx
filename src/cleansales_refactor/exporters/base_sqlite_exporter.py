import logging
from abc import ABC, abstractmethod
from typing import Any, Callable, Generic, TypeVar

from sqlmodel import Session, SQLModel, create_engine, select

from ..models import ProcessingResult, SourceData
from ..models.orm_models import BaseEventSource, ErrorRecord, ORMModel, ProcessingEvent
from .exporter_interface import IExporter

logger = logging.getLogger(__name__)

T = TypeVar("T")
M = TypeVar("M", bound=ORMModel)
ES = TypeVar("ES", bound=BaseEventSource[Any])


class BaseSQLiteExporter(Generic[T, M, ES], IExporter[T], ABC):
    """基礎 SQLite 匯出服務"""

    def __init__(self, db_path: str) -> None:
        self.db_path = db_path
        self._engine = create_engine(f"sqlite:///{db_path}", echo=False)
        self._init_database()

    def _init_database(self) -> None:
        """初始化資料庫表格"""
        SQLModel.metadata.create_all(self._engine)

    def _get_session(self) -> Session:
        """取得 Session"""
        return Session(self._engine)

    def export_data(
        self, source_data: SourceData, data: ProcessingResult[T]
    ) -> dict[str, Any]:
        """匯出資料至 SQLite (實作 IExporter 介面)"""
        if not data.processed_data:
            return {
                "status": "error",
                "msg": "No data to export",
            }

        session = self._get_session()
        try:
            all_existing_keys: set[str] = self._get_all_existing_keys(session)
            all_records_dict = {
                self.get_unique_key(record): record for record in data.processed_data
            }
            all_records_keys = set(all_records_dict.keys())
            keys_to_save = all_records_keys - all_existing_keys
            keys_to_delete = all_existing_keys - all_records_keys

            # 處理新增記錄
            if keys_to_save:
                save_event_source = self._handle_save_event(
                    keys_to_save,
                    lambda key: self._record_to_orm(all_records_dict[key]),
                    ProcessingEvent.ADDED,
                    source_data,
                )
                if save_event_source:
                    session.merge(save_event_source)

            # 處理刪除記錄
            if keys_to_delete:
                delete_event_source = self._handle_save_event(
                    keys_to_delete,
                    lambda key: session.get(self._get_orm_class(), key),
                    ProcessingEvent.DELETED,
                    source_data,
                )
                if delete_event_source:
                    session.merge(delete_event_source)

            session.commit()

            logger.info("資料匯出成功")
            return {
                "success": True,
                "msg": f"儲存 {len(keys_to_save)} 筆資料，刪除 {len(keys_to_delete)} 筆資料",
            }
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

    def _handle_save_event(
        self,
        keys: set[str],
        get_data_func: Callable[[str], ORMModel | None],
        event_value: ProcessingEvent,
        source_data: SourceData,
    ) -> ES:
        models_to_process: list[ORMModel] = []
        for key in keys:
            model_to_process = get_data_func(key)
            if model_to_process is None:
                continue
            model_to_process.event = event_value
            models_to_process.append(model_to_process)
        event_source = self._get_event_source_class()(
            source_name=source_data.file_name,
            source_md5=source_data.md5,
            event=event_value,
        )
        event_source.records = models_to_process
        return event_source

    def _get_all_existing_keys(self, session: Session) -> set[str]:
        """取得所有已存在的唯一識別碼"""
        orm_class = self._get_orm_class()
        primary_key = self._get_primary_key_field()
        stmt = select(orm_class).where(orm_class.event == ProcessingEvent.ADDED)
        models = session.exec(stmt).all()
        return set(getattr(model, primary_key) for model in models)

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
    def _get_event_source_class(self) -> type[ES]:
        """取得事件來源類別"""
        pass

    @abstractmethod
    def _get_primary_key_field(self) -> str:
        """取得主鍵欄位名稱"""
        pass
