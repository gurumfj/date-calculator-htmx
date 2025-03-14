import hashlib
import logging
from abc import ABC, abstractmethod
from collections.abc import Generator
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

import pandas as pd
from pydantic import BaseModel, Field
from sqlmodel import Session, SQLModel, create_engine, select

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
    data: dict[str, Any]


class IProcessor(ABC):
    _session: Session

    def __init__(self, db_path: Path) -> None:
        db_dir = db_path.parent
        if not db_dir.exists():
            db_dir.mkdir(parents=True)

        _engine = create_engine(f"sqlite:///{db_path}", echo=False)
        SQLModel.metadata.create_all(_engine)
        logger.info(f"Database created at {db_path}")

        # 建立 Session 工廠
        self._session = Session(_engine)

    def get_session(self) -> Generator[Session, Any, None]:
        with self._session as session:
            yield session

    def execute(
        self, source: SourceData | Path | pd.DataFrame, check_md5: bool = True
    ) -> IResponse:
        try:
            df = None
            if isinstance(source, SourceData):
                df = source.dataframe
            elif isinstance(source, Path):
                df = pd.read_excel(source.resolve())
            else:
                df = source

            md5 = hashlib.md5(df.to_csv(index=False).encode("utf-8")).hexdigest()

            if check_md5 and self._is_md5_exist(md5):
                logger.info("MD5 already exists, skipping execution")
                return IResponse(success=True, message="MD5 already exists", data={})

            validated_records, error_records = self._validate_data(df)

            self._infrastructure(validated_records, error_records, md5)

            return IResponse(
                success=True,
                message=f"{len(validated_records)} records validated, {len(error_records)} records failed validation",
                data={},
            )
        except FileNotFoundError:
            logger.error(f"File not found: {source}")
            raise
        except Exception as e:
            logger.error(f"Error during execution: {e}")
            raise e

    def _is_md5_exist(self, md5: str) -> bool:
        with self._session as session:
            orm_schema = self.set_orm_schema()
            stmt = select(orm_schema).where(orm_schema.md5 == md5)
            result = session.exec(stmt).first()
            return result is not None

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
        # try:
        validator_schema: type[IBaseModel] = self.set_validator_schema()

        validated_records: dict[str, IBaseModel] = {}
        error_records = []

        # 將每筆資料轉換為 SaleRecordBase 物件
        for _, row in df.iterrows():
            try:
                # print(row)
                record = validator_schema.model_validate(row)
                record.unique_id = (
                    self._calculate_unique_id(record)
                    if record.unique_id is None
                    else record.unique_id
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
        # except Exception as e:
        #     logger.error(f"資料驗證失敗: {e}")
        #     raise e

    def _infrastructure(
        self,
        validated_records: dict[str, IBaseModel],
        error_records: list[dict[str, Any]],
        md5: str,
    ) -> None:
        with self._session as session:
            try:
                orm_schema = self.set_orm_schema()
                # 查詢資料庫中所有的記錄
                get_all_stmt = select(orm_schema).where(
                    orm_schema.event == RecordEvent.ADDED
                )
                all_db_obj = session.exec(get_all_stmt).all()

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
                    return

                # 只添加不在資料庫中的記錄
                for new_key in new_keys:
                    orm_record = orm_schema.model_validate(validated_records[new_key])
                    orm_record.event = RecordEvent.ADDED
                    orm_record.md5 = md5
                    _ = session.merge(orm_record)
                session.commit()
                logger.info(f"成功添加 {len(new_keys)} 條記錄")

            except Exception as e:
                session.rollback()
                logger.error(f"添加記錄時發生錯誤: {e}")
                raise

    @abstractmethod
    def set_validator_schema(self) -> type[IBaseModel]:
        pass

    @abstractmethod
    def set_orm_schema(self) -> type[IORMModel]:
        pass

    @abstractmethod
    def set_response_schema(self) -> type[IResponse]:
        pass
