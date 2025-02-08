import logging
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Callable, Generic, TypeVar

from sqlmodel import Session, desc, select

from ..shared.models import ProcessingResult, SourceData
from .exporter_interface import IExporter
from .orm_models import BaseEventSource, ErrorRecord, ORMModel, ProcessingEvent

logger = logging.getLogger(__name__)

T = TypeVar("T")
M = TypeVar("M", bound=ORMModel)
ES = TypeVar("ES", bound=BaseEventSource[Any])


class BaseSQLiteExporter(Generic[T, M, ES], IExporter[T], ABC):
    """基礎 SQLite 匯出服務"""

    def execute(
        self,
        processed_result: ProcessingResult[T],
        session: Session | None = None,
    ) -> dict[str, int]:
        """執行匯出服務"""
        if session is None:
            raise ValueError("session is required")
        try:
            added_event_source, deleted_event_source = self.export_data(
                session=session,
                source_data=processed_result.source_data,
                data=processed_result,
            )
            error_records = self.export_errors(session=session, data=processed_result)
            session.commit()
            return {
                "added": added_event_source.count if added_event_source else 0,
                "deleted": deleted_event_source.count if deleted_event_source else 0,
                "unvalidated": len(error_records),
            }
        except Exception as e:
            logger.error(f"匯出資料時發生錯誤: {e}")
            session.rollback()
            raise e

    def export_data(
        self,
        session: Session,
        source_data: SourceData,
        data: ProcessingResult[T],
    ) -> tuple[ES, ES]:
        """匯出資料至 SQLite (實作 IExporter 介面)"""
        all_existing_keys: set[str] = self._get_all_existing_keys(session)
        all_records_dict = {
            self.get_unique_key(record): record for record in data.processed_data
        }
        all_records_keys = set(all_records_dict.keys())
        keys_to_save = all_records_keys - all_existing_keys
        keys_to_delete = all_existing_keys - all_records_keys

        # 處理新增記錄
        added_event_source = self._handle_save_event(
            keys=keys_to_save,
            get_data_func=lambda key: self._record_to_orm(all_records_dict[key]),
            event_value=ProcessingEvent.ADDED,
            source_data=source_data,
        )
        session.merge(added_event_source)
        # 處理刪除記錄
        deleted_event_source = self._handle_save_event(
            keys=keys_to_delete,
            get_data_func=lambda key: session.get(self._get_orm_class(), key),
            event_value=ProcessingEvent.DELETED,
            source_data=source_data,
        )
        session.merge(deleted_event_source)

        return added_event_source, deleted_event_source

    def export_errors(
        self, session: Session, data: ProcessingResult[T]
    ) -> list[ErrorRecord]:
        """匯出錯誤記錄 (實作 IExporter 介面)"""
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
        return error_records

    def is_source_md5_exists_in_latest_record(
        self, session: Session, source_data: SourceData
    ) -> bool:
        # 最新的md5
        stmt = (
            select(self._get_event_source_class().source_md5)
            .where(self._get_event_source_class().event == ProcessingEvent.NEW_MD5)
            .order_by(desc(self._get_event_source_class().id))
            .limit(1)
        )
        result = session.exec(stmt).first()
        logger.debug(f"最新的md5: {result}")
        logger.debug(f"來源的md5: {source_data.md5}")
        is_exists = result is not None and source_data.md5 == result
        if is_exists:
            logger.debug("md5 已存在")
        else:
            logger.debug("md5 不存在")
            event_source = self._handle_save_event(
                keys=set(),
                get_data_func=lambda key: None,
                event_value=ProcessingEvent.NEW_MD5,
                source_data=source_data,
            )
            session.add(event_source)
            session.commit()
        return is_exists

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
            model_to_process.updated_at = datetime.now()
            models_to_process.append(model_to_process)
        event_source = self._get_event_source_class()(
            source_name=source_data.file_name,
            source_md5=source_data.md5,
            event=event_value,
            count=len(models_to_process),
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
