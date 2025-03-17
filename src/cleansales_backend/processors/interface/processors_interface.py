import hashlib
import logging
from abc import ABC, abstractmethod
from collections.abc import Sequence
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Generic, Literal, TypeVar

import pandas as pd
from pydantic import BaseModel, Field
from sqlmodel import Session, SQLModel, col, select

from cleansales_backend.shared.models import SourceData

logger = logging.getLogger(__name__)


class RecordEvent(Enum):
    """事件類型"""

    ADDED = "added"
    DELETED = "deleted"
    UPDATED = "updated"


class IBaseModel(BaseModel):
    unique_id: str | None = Field(default=None)


class IORMModel(SQLModel):
    unique_id: str
    md5: str | None = Field(default=None)
    event: RecordEvent | None = Field(default=None)
    updated_at: datetime = Field(default_factory=datetime.now)


class IResponse(SQLModel):
    success: bool
    message: str
    content: dict[str, Any] = Field(default_factory=dict)


ORMT = TypeVar("ORMT", bound=IORMModel)
VT = TypeVar("VT", bound=IBaseModel)
RT = TypeVar("RT", bound=IResponse)


class IProcessor(ABC, Generic[ORMT, VT, RT]):
    _orm_schema: type[ORMT]
    _validator_schema: type[VT]
    _response_schema: type[RT]

    @abstractmethod
    def set_validator_schema(self) -> type[VT]:
        pass

    @abstractmethod
    def set_orm_schema(self) -> type[ORMT]:
        pass

    @abstractmethod
    def set_response_schema(self) -> type[RT]:
        pass

    def __init__(self) -> None:
        self._orm_schema = self.set_orm_schema()
        self._validator_schema = self.set_validator_schema()
        self._response_schema = self.set_response_schema()

    def execute(
        self,
        session: Session,
        source: SourceData | Path | pd.DataFrame,
        check_md5: bool = True,
    ) -> RT:
        try:
            df = None
            if isinstance(source, SourceData):
                df = source.dataframe
            elif isinstance(source, Path):
                df = pd.read_excel(source.resolve())
            else:
                df = source

            md5 = hashlib.md5(df.to_csv(index=False).encode("utf-8")).hexdigest()

            if check_md5 and self._is_md5_exist(session, md5):
                logger.info("MD5 already exists, skipping execution")
                return self._response_schema(
                    success=False, message="MD5 already exists", content={}
                )

            validated_records, error_records = self._validate_data(df)

            new_keys, delete_keys = self._infrastructure(session, validated_records, error_records, md5)

            return self._response_schema(
                success=True,
                message="\n".join([
                    f"{len(validated_records)} records validated",
                    f"{len(error_records)} records failed validation",
                    f"{len(new_keys)} records to be added" if new_keys else "no records to be added",
                    f"{len(delete_keys)} records to be deleted" if delete_keys else "no records to be deleted",
                ]),
                content={
                    "timestamp": datetime.now().isoformat(),
                    "file": source.file_name or source.name or source.absolute() or "Unknown",
                    "validated_records": len(validated_records),
                    "error_records": len(error_records),
                    "new_keys": len(new_keys),
                    "delete_keys": len(delete_keys),
                },
            )
        except FileNotFoundError:
            logger.error(f"File not found: {source}")
            raise
        except Exception as e:
            logger.error(f"Error during execution: {e}")
            raise e

    def _is_md5_exist(self, session: Session, md5: str) -> bool:
        result = self._get_by_criteria(session, {"md5": (md5, "eq")})
        return len(result) > 0

    def _calculate_unique_id(self, record: IBaseModel) -> str:
        return hashlib.sha256(
            record.model_dump_json(exclude={"unique_id"}).encode()
        ).hexdigest()[:10]

    def _validate_data(
        self,
        df: pd.DataFrame,
    ) -> tuple[dict[str, IBaseModel], list[dict[str, Any]]]:
        """Validate data from DataFrame.

        Args:
            df (pd.DataFrame): DataFrame to validate.

        Returns:
            tuple[dict[str, IBaseModel], list[dict[str, Any]]]: Tuple of validated records and error records.
        """

        validated_records: dict[str, IBaseModel] = {}
        error_records = []

        # 將每筆資料轉換為 SaleRecordBase 物件
        for _, row in df.iterrows():
            try:
                # print(row)
                record = self._validator_schema.model_validate(row)
                # validated_records.setdefault(record.unique_id or self._calculate_unique_id(record), record)
                record.unique_id = (
                    self._calculate_unique_id(record) or record.unique_id
                    # if record.unique_id is None
                    # else record.unique_id
                )
                validated_records[record.unique_id] = record
            except ValueError:
                error = {
                    "message": "轉換資料時發生錯誤",
                    "data": row.to_dict(),
                    # "error": str(ve),
                }
                logger.debug(f"資料驗證失敗: {error}")
                error_records.append(error)
        logger.info(
            f"{len(validated_records)} records validated, {len(error_records)} records failed validation"
        )
        return validated_records, error_records

    def _infrastructure(
        self,
        session: Session,
        validated_records: dict[str, IBaseModel],
        error_records: list[dict[str, Any]],
        md5: str,
    ) -> tuple[set[str], set[str]]:
        try:
            if not validated_records:
                logger.info("沒有有效記錄")
                return set(), set()
            # 查詢資料庫中所有的記錄
            all_db_obj: list[ORMT] = session.exec(select(self._orm_schema).where(
                self._orm_schema.event == RecordEvent.ADDED
            )).all()

            # 從完整對象中提取 unique_id
            db_keys: set[str] = set(r.unique_id for r in all_db_obj)
            import_keys: set[str] = set(validated_records.keys())
            delete_keys: set[str] = db_keys - import_keys
            new_keys: set[str] = import_keys - db_keys

            logger.info(f"{len(import_keys)} records in import file")
            logger.info(f"{len(new_keys)} records to be added")
            logger.info(f"{len(delete_keys)} records to be deleted")

            # 刪除不在 import file 中的記錄
            for obj in all_db_obj:
                if obj.unique_id in delete_keys:
                    # session.delete(obj)
                    obj.event = RecordEvent.DELETED
                    obj.updated_at = datetime.now()
                    _ = session.merge(obj)

            if not new_keys:
                logger.info("沒有新記錄需要添加")
                session.commit()
                return set(), set()

            # 只添加不在資料庫中的記錄
            for new_key in new_keys:
                orm_record = self._orm_schema.model_validate(validated_records[new_key])
                orm_record.event = RecordEvent.ADDED
                orm_record.md5 = md5
                _ = session.merge(orm_record)
            session.commit()
            logger.info(f"成功添加 {len(new_keys)} 條記錄")

            return new_keys, delete_keys

        except Exception as e:
            session.rollback()
            logger.error(f"添加記錄時發生錯誤: {e}")
            raise

    def _get_by_criteria(
        self,
        session: Session,
        criteria: dict[str, tuple[Any, Literal["eq", "in"]]] | None = None,
    ) -> Sequence[ORMT]:
        stmt = select(self._orm_schema)
        if criteria:
            for key, (value, operator) in criteria.items():
                if operator == "eq":
                    stmt = stmt.where(getattr(self._orm_schema, key) == value)
                elif operator == "in":
                    stmt = stmt.where(col(getattr(self._orm_schema, key)).in_(value))
        result = session.exec(stmt).all()
        return result
