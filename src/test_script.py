import logging
from pathlib import Path
from typing import Any

import pandas as pd
from sqlalchemy import create_engine
from sqlmodel import Session, SQLModel, select

from cleansales_backend.processors.validator_schema import (
    SaleRecordBase,
    # SaleRecordORM,
)
from cleansales_backend.processors.validator_schema.sales_schema import SaleRecordORM

logger = logging.getLogger(__name__)


def init_db(db_path: str) -> Session:
    # 檢查並建立資料庫目錄
    db_dir = Path(db_path).parent
    if not db_dir.exists():
        db_dir.mkdir(parents=True)

    _engine = create_engine(f"sqlite:///{db_path}", echo=False)
    SQLModel.metadata.create_all(_engine)
    logger.info(f"Database created at {db_path}")

    # 建立 Session 工廠
    return Session(_engine)


# 讀取 Excel 檔案並輸出 SaleRecordORM
# 參數: file_path - Excel 檔案路徑
def read_excel_and_print_records(
    file_path: str,
) -> tuple[dict[str, SaleRecordBase], list[dict[str, Any]]]:
    # 讀取 Excel 檔案
    df = pd.read_excel(file_path)

    validated_records: dict[str, SaleRecordBase] = {}
    error_records = []

    # 將每筆資料轉換為 SaleRecordBase 物件
    for _, row in df.iterrows():
        try:
            # print(row)
            record = SaleRecordBase.model_validate(row)
            # print(record.model_dump())
            validated_records[record.unique_id] = record
        except Exception as e:
            error = {
                "message": "轉換資料時發生錯誤",
                "data": row.to_dict(),
                "error": str(e),
            }
            # print(error)
            error_records.append(error)

    print(f"========== {len(validated_records)} records validated")
    return validated_records, error_records


def infrastructure(v: dict[str, SaleRecordBase], e: list[dict[str, Any]]) -> None:
    with init_db(
        "/Users/pierrewu/code/cleansales-dockerize/backend/data/test.db"
    ) as session:
        try:
            # 查詢資料庫中所有的記錄
            get_all_stmt = select(SaleRecordORM)
            result = session.exec(get_all_stmt).all()

            # 從完整對象中提取 unique_id
            db_keys: set[str] = set(r.unique_id for r in result)
            print(f"========== {len(db_keys)} records in database")
            import_keys: set[str] = set(v.keys())
            new_keys: set[str] = import_keys - db_keys

            print(f"========== {len(import_keys)} records in import file")
            print(f"========== {len(new_keys)} records to be added")

            # 只添加不在資料庫中的記錄
            new_records: list[SaleRecordORM] = [
                SaleRecordORM.model_validate(r)
                for r in v.values()
                if r.unique_id in new_keys
            ]

            if not new_records:
                print("沒有新記錄需要添加")
                return

            session.add_all(new_records)
            session.commit()
            print(f"成功添加 {len(new_records)} 條記錄")
        except Exception as e:
            session.rollback()
            print(f"添加記錄時發生錯誤: {e}")
            raise


# 主程式入口
if __name__ == "__main__":
    # 測試讀取 Excel 檔案
    file: Path = Path(
        "/Users/pierrewu/Library/CloudStorage/CloudMounter-福泉dropbox/Documents/販售/販售全單(結案正常版).xlsx"
    )
    SessionLocal = init_db(
        "/Users/pierrewu/code/cleansales-dockerize/backend/data/test.db"
    )
    v, e = read_excel_and_print_records(str(file.resolve()))
    infrastructure(v, e)
