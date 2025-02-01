import logging
import time
from pathlib import Path
from typing import Any, Callable, TypeAlias

import pandas as pd

from cleansales_refactor.exporters.sqlite_exporter import SQLiteExporter
from cleansales_refactor.models import ProcessingResult, SaleRecord
from cleansales_refactor.processor.sale_record_processor import SalesProcessor
from cleansales_refactor.services import IExporter, IProcessor

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# 添加控制台處理器
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)

# 設置日誌格式
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
console_handler.setFormatter(formatter)

# 添加處理器到 logger
logger.addHandler(console_handler)

DataReader: TypeAlias = Callable[[], pd.DataFrame]
DataProcessor: TypeAlias = Callable[[pd.DataFrame], ProcessingResult[SaleRecord]]
DataExporter: TypeAlias = Callable[[ProcessingResult[SaleRecord]], None]


def time_it(func: Callable[..., Any]) -> Callable[..., Any]:
    """計時函數"""

    def wrapper(*args: Any, **kwargs: Any) -> Any:
        time_start = time.time()
        result = func(*args, **kwargs)
        time_end = time.time()
        logger.debug(f"{func.__name__}函數執行時間: {time_end - time_start}")
        return result

    return wrapper


def create_excel_reader(
    file_path: str | Path, sheet_name: str = "工作表1"
) -> DataReader:
    """建立 Excel 讀取函數"""

    def read_data() -> pd.DataFrame:
        df = pd.read_excel(file_path, sheet_name=sheet_name)
        return df
    return time_it(read_data)


def create_data_processor(processor: IProcessor[SaleRecord]) -> DataProcessor:
    """建立資料處理函數"""

    def process_data(df: pd.DataFrame) -> ProcessingResult[SaleRecord]:
        result = processor.process_data(df)
        return result

    return time_it(process_data)


def create_data_exporter(exporter: IExporter[SaleRecord]) -> DataExporter:
    """建立資料匯出函數"""

    def export_data(result: ProcessingResult[SaleRecord]) -> None:
        exporter.export_data(result)
        exporter.export_errors(result)

    return time_it(export_data)


def create_sales_data_pipeline(
    input_file: str | Path, db_path: str | Path, sheet_name: str = "工作表1"
) -> Callable[[], None]:
    """建立銷售資料處理管道

    Args:
        input_file: Excel 檔案路徑
        db_path: SQLite 資料庫路徑
        sheet_name: Excel 工作表名稱

    Returns:
        一個無參數的函數，執行完整的資料處理流程
    """
    reader = create_excel_reader(input_file, sheet_name)
    processor = create_data_processor(SalesProcessor)
    exporter = create_data_exporter(SQLiteExporter(str(db_path)))

    def pipeline() -> None:
        try:
            exporter(processor(reader()))
        except Exception as e:
            logger.error(f"處理銷售資料時發生錯誤: {e}")
            raise

    return pipeline


def sales_data_service() -> None:
    """銷售資料服務"""
    input_file = "sales_sample.xlsx"
    db_path = "sales_data.db"

    pipeline = create_sales_data_pipeline(input_file, db_path)
    pipeline()


if __name__ == "__main__":
    sales_data_service()
