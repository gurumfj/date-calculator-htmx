import hashlib
import logging
from abc import ABC, abstractmethod
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date, datetime
from enum import Enum
from pathlib import Path
from typing import Any, Generic, Literal, TypeVar

import pandas as pd
from pydantic import BaseModel
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import (
    Column,
    Field,
    Session,
    SQLModel,
    col,
    desc,
    select,
)

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
    batch_name: str


@dataclass
class ValidationResponse:
    data_existed: bool
    validated_records: dict[str, IBaseModel]
    error_records: list[dict[str, Any]]


@dataclass
class InfrastructureResponse:
    new_keys: set[str]
    new_names: set[str]
    delete_keys: set[str]
    delete_names: set[str]


@dataclass
class ResponseContent:
    processor_name: str
    validation: ValidationResponse
    infrastructure: InfrastructureResponse | None = None


class IResponse(SQLModel):
    success: bool
    content: ResponseContent


ORMT = TypeVar("ORMT", bound=IORMModel)
VT = TypeVar("VT", bound=IBaseModel)
# RT = TypeVar("RT", bound=IResponse)


class BatchAggregateORM(SQLModel, table=True):
    __tablename__: str = "batchaggregates"
    # 索引
    # id: int | None = Field(default=None, primary_key=True)
    batch_name: str = Field(description="批次名稱", primary_key=True)
    chicken_breed: str = Field(description="雞種")

    # 資料範圍
    initial_date: date = Field(description="初始日期")
    final_date: date = Field(description="最終日期")

    # 最後異動 table
    updated_at: datetime = Field(default_factory=datetime.now)
    updated_by_table: str | None = Field(default=None, description="最後異動表格")
    updated_by_record: str | None = Field(default=None, description="最後異動記錄")
    # 前端更新欄位 jsonb
    data: dict[str, Any] | None = Field(
        default=None, description="前端欄位", sa_column=Column(JSONB)
    )


class IProcessor(ABC, Generic[ORMT, VT]):
    @abstractmethod
    def set_processor_name(self) -> str:
        pass

    @abstractmethod
    def set_validator_schema(self) -> type[VT]:
        pass

    @abstractmethod
    def set_orm_schema(self) -> type[ORMT]:
        pass

    @abstractmethod
    def set_orm_foreign_key(self) -> str:
        pass

    @abstractmethod
    def set_orm_date_field(self) -> str:
        pass

    @abstractmethod
    def set_orm_chicken_breed(self) -> str | None:
        pass

    def get_all_orm(self, session: Session) -> Sequence[ORMT]:
        _orm = self.set_orm_schema()
        stmt = select(_orm).where(_orm.event == RecordEvent.ADDED)
        return session.exec(stmt).all()

    def _get_df(self, source: SourceData | Path | pd.DataFrame) -> pd.DataFrame:
        if isinstance(source, SourceData):
            return source.dataframe
        elif isinstance(source, Path):
            return pd.read_excel(source.resolve())
        else:
            return source

    def _create_response(
        self,
        success: bool,
        processor_name: str,
        validation: ValidationResponse,
        infrastructure: InfrastructureResponse | None = None,
    ) -> IResponse:
        return IResponse(
            success=success,
            content=ResponseContent(
                processor_name=processor_name,
                validation=validation,
                infrastructure=infrastructure,
            ),
        )

    def execute(
        self,
        session: Session,
        source: SourceData | Path | pd.DataFrame,
        check_md5: bool = True,
    ) -> IResponse:
        try:
            df = self._get_df(source)
            md5 = hashlib.md5(df.to_csv(index=False).encode("utf-8")).hexdigest()

            if check_md5 and self._is_md5_exist(session, md5):
                logger.info("MD5 already exists, skipping execution")
                return self._create_response(
                    success=False,
                    processor_name=self.set_processor_name(),
                    validation=ValidationResponse(
                        data_existed=True,
                        validated_records={},
                        error_records=[],
                    ),
                    infrastructure=None,
                )

            validated_records, error_records = self._validate_data(df)

            infrastructure_response = self._infrastructure(
                session, validated_records, error_records, md5
            )
            return self._create_response(
                success=True,
                processor_name=self.set_processor_name(),
                validation=ValidationResponse(
                    data_existed=False,
                    validated_records=validated_records,
                    error_records=error_records,
                ),
                infrastructure=infrastructure_response,
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
            record.model_dump_json(exclude={"unique_id", "is_completed"}).encode()
        ).hexdigest()[:10]

    def _validate_data(
        self,
        df: pd.DataFrame,
    ) -> tuple[dict[str, IBaseModel], list[dict[str, Any]]]:
        """Validate data from DataFrame.

        Args:
            df (pd.DataFrame): DataFrame to validate.

        Returns:
            tuple[dict[str, IBaseModel], list[dict[str, Any]]]:
            Tuple of validated records and error records.
        """
        _validator_schema = self.set_validator_schema()
        validated_records: dict[str, IBaseModel] = {}
        error_records: list[dict[str, Any]] = []

        # 將每筆資料轉換為 IBaseModel 物件
        for _, row in df.iterrows():
            try:
                # 嘗試驗證資料
                record = _validator_schema.model_validate(row)
                record.unique_id = record.unique_id or self._calculate_unique_id(record)
                validated_records[record.unique_id] = record
            except ValueError as ve:
                # 記錄詳細的錯誤信息
                error: dict[str, Any] = {
                    "message": "轉換資料時發生錯誤",
                    "data": row.to_dict(),
                    "error": str(ve),
                }
                logger.debug(f"資料驗證失敗詳細錯誤: {str(ve)}")
                logger.debug(f"資料驗證失敗: {error}")
                error_records.append(error)
        logger.info(
            f"{len(validated_records)} records validated,\n+\
             {len(error_records)} records failed validation"
        )
        return validated_records, error_records

    def _infrastructure(
        self,
        session: Session,
        validated_records: dict[str, IBaseModel],
        error_records: list[dict[str, Any]],
        md5: str,
    ) -> InfrastructureResponse:
        _ = error_records
        _orm = self.set_orm_schema()
        _date_field = self.set_orm_date_field()
        _foreign_key = self.set_orm_foreign_key()
        if not validated_records:
            logger.info("沒有有效記錄")
            return InfrastructureResponse(
                new_keys=set(),
                new_names=set(),
                delete_keys=set(),
                delete_names=set(),
            )

        # 查詢資料庫中所有的記錄
        all_db_obj = session.exec(
            select(_orm)
            # .where(
            #     self.set_orm_schema().event == RecordEvent.ADDED
            # )
        ).all()

        # 從完整對象中提取 unique_id
        db_keys: set[str] = set(r.unique_id for r in all_db_obj)
        import_keys: set[str] = set(validated_records.keys())
        delete_keys: set[str] = db_keys - import_keys
        new_keys: set[str] = import_keys - db_keys

        logger.info(f"{len(import_keys)} records in import file")
        logger.info(f"{len(new_keys)} records to be added")
        logger.info(f"{len(delete_keys)} records to be deleted")

        # 刪除不在 import file 中的記錄
        deleted_names: set[str] = set()
        for obj in all_db_obj:
            if obj.unique_id in delete_keys:
                # session.delete(obj)
                obj.event = RecordEvent.DELETED
                obj.updated_at = datetime.now()
                deleted_names.add(getattr(obj, _foreign_key))
                session.delete(obj)

        if not new_keys and not delete_keys:
            logger.info("沒有記錄變動")
            return InfrastructureResponse(
                new_keys=new_keys,
                new_names=set(),
                delete_keys=delete_keys,
                delete_names=deleted_names,
            )

        # 只添加不在資料庫中的記錄
        new_names: set[str] = set()
        for new_key in new_keys:
            orm_record = _orm.model_validate(validated_records[new_key])
            orm_record.event = RecordEvent.ADDED
            orm_record.md5 = md5
            _ = session.merge(orm_record)
            new_names.add(getattr(orm_record, _foreign_key))

            # 更新批次統計
            _ = self.update_batch_aggregate(session, orm_record)

        logger.info(f"成功添加 {len(new_keys)} 條記錄")
        return InfrastructureResponse(
            new_keys=new_keys,
            new_names=new_names,
            delete_keys=delete_keys,
            delete_names=deleted_names,
        )

    def execute_update_batch_aggregate(self, session: Session) -> None:
        """腳本使用"""
        _orm = self.set_orm_schema()
        _date_field = self.set_orm_date_field()
        batches = session.exec(select(BatchAggregateORM)).all()
        for batch in batches:
            final_record = session.exec(
                select(_orm)
                .where(_orm.batch_name == batch.batch_name)
                .order_by(desc(getattr(_orm, _date_field)))
            ).first()
            if not final_record:
                continue
            _ = self.update_batch_aggregate(session, final_record)

    def update_batch_aggregate(
        self, session: Session, orm: ORMT
    ) -> BatchAggregateORM | None:
        """更新批次統計"""
        _chicken_breed = self.set_orm_chicken_breed()
        _date_field = self.set_orm_date_field()
        stmt = select(BatchAggregateORM).where(
            BatchAggregateORM.batch_name == orm.batch_name
        )
        result = session.exec(stmt).one_or_none()
        if not result:
            if _chicken_breed is None:
                # 不從販售表創建新的批次統計
                return None

            result = BatchAggregateORM(
                batch_name=orm.batch_name,
                chicken_breed=getattr(orm, _chicken_breed),
                initial_date=getattr(orm, _date_field),
                final_date=getattr(orm, _date_field),
                updated_at=datetime.now(),
                updated_by_table=str(orm.__tablename__),
                updated_by_record=orm.unique_id,
            )
            return session.merge(result)
        elif getattr(orm, _date_field) > result.final_date:
            result.final_date = getattr(orm, _date_field)
            result.updated_at = datetime.now()
            result.updated_by_table = orm.__tablename__  # type: ignore
            result.updated_by_record = orm.unique_id
            return session.merge(result)
        return result

    def _get_by_criteria(
        self,
        session: Session,
        criteria: dict[str, tuple[Any, Literal["eq", "in"]]] | None = None,
    ) -> Sequence[ORMT]:
        stmt = select(self.set_orm_schema())
        if criteria:
            for key, (value, operator) in criteria.items():
                if operator == "eq":
                    stmt = stmt.where(getattr(self.set_orm_schema(), key) == value)
                elif operator == "in":
                    stmt = stmt.where(
                        col(getattr(self.set_orm_schema(), key)).in_(value)
                    )
        result = session.exec(stmt).all()
        return result

    def get_foreign_key_by_unique_id(
        self, session: Session, unique_id: str
    ) -> str | None:
        stmt = select(self.set_orm_schema()).where(
            self.set_orm_schema().unique_id == unique_id
        )
        result = session.exec(stmt).one_or_none()
        return getattr(result, self.set_orm_foreign_key()) if result else None
