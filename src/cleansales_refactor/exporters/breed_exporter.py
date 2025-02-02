from dataclasses import asdict
from datetime import datetime
from typing import Callable, Iterable, TypeVar

from sqlmodel import Field, Session, SQLModel, create_engine, select

from ..models import BreedRecord, ProcessingResult
from .exporter_interface import IExporter

T = TypeVar("T")


class BreedRecordORM(SQLModel, table=True):
    """入雛記錄資料表模型"""

    unique_id: str = Field(default=None, primary_key=True, index=True, unique=True)

    # 基本資料
    farm_name: str | None
    address: str | None
    farm_license: str | None

    # 畜主資料
    farmer_name: str | None
    farmer_address: str | None

    # 批次資料
    batch_name: str | None
    veterinarian: str | None
    chicken_breed: str | None
    male: int | None
    female: int | None
    breed_date: datetime | None
    supplier: str | None
    sub_location: str | None
    is_completed: str | None
    created_at: datetime = Field(default_factory=datetime.now)


class BreedSQLiteExporter(IExporter[BreedRecord]):
    """入雛記錄匯出服務 (使用 SQLite)"""

    def __init__(self, db_path: str) -> None:
        self.db_path = db_path
        self._engine = create_engine(f"sqlite:///{db_path}", echo=False)
        self._init_database()

    def _init_database(self) -> None:
        """初始化資料庫表格"""
        SQLModel.metadata.create_all(self._engine)

    def export_data(self, data: ProcessingResult[BreedRecord]) -> None:
        """匯出入雛記錄"""

        with Session(self._engine) as session:
            all_existing_keys: set[str] = self._get_all_existing_keys(session)
            all_records_keys: set[str] = set(
                record.unique_id for record in data.processed_data
            )
            all_records_dict: dict[str, BreedRecord] = {
                record.unique_id: record for record in data.processed_data
            }

            # 儲存不存在於Database的records
            self._for_each(
                self._filter_key_not_exists(all_records_keys, all_existing_keys),
                lambda key: self._save_data(session, all_records_dict[key]),
            )

            # 刪除不存在於ProcessingResult的模型key
            self._for_each(
                self._filter_key_not_exists(all_existing_keys, all_records_keys),
                lambda key: self._delete_data_by_key(session, key),
            )

            session.commit()

    def export_errors(self, data: ProcessingResult[BreedRecord]) -> None:
        """匯出錯誤記錄"""
        pass

    def _save_data(self, session: Session, record: BreedRecord) -> None:
        print(f"儲存資料: {record}")
        session.add(self._record_to_orm(record))

    def _delete_data_by_key(self, session: Session, key: str) -> None:
        """刪除唯一識別碼"""
        print(f"刪除唯一識別碼: {key}")
        model_to_delete: BreedRecordORM | None = session.get(BreedRecordORM, key)
        if model_to_delete:
            session.delete(model_to_delete)

    def _get_all_existing_keys(self, session: Session) -> set[str]:
        """取得所有已存在的唯一識別碼"""
        return set(session.exec(select(BreedRecordORM.unique_id)).all())

    """
    Caculation functions
    """

    def _for_each(self, iterable: Iterable[T], func: Callable[[T], None]) -> None:
        """對每個元素執行函數"""
        for item in iterable:
            func(item)

    def _filter_key_not_exists(
        self, keys_to_compare: set[str], exist_keys: set[str]
    ) -> set[str]:
        # return set(filter(lambda key: key not in exist_keys, keys_to_compare))
        return keys_to_compare - exist_keys

    def _record_to_orm(self, record: BreedRecord) -> BreedRecordORM:
        """將入雛記錄轉換為資料表模型"""
        return BreedRecordORM(
            **{k: v for k, v in asdict(record).items() if v is not None}
            | {"unique_id": record.unique_id}
        )

    def _orm_to_record(self, orm: BreedRecordORM) -> BreedRecord:
        """將資料表模型轉換為入雛記錄"""
        return BreedRecord(**orm.__dict__)
