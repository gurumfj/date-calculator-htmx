from dataclasses import dataclass
import hashlib
import io
import logging
import time
from pathlib import Path
from typing import Any, Callable, TypeAlias, TypeVar

import pandas as pd

from cleansales_refactor.exporters import (
    BreedSQLiteExporter,
    IExporter,
    SaleSQLiteExporter,
)
from cleansales_refactor.models import ProcessingResult
from cleansales_refactor.processor import BreedsProcessor, IProcessor, SalesProcessor

# 設定根 logger
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)

logger = logging.getLogger(__name__)

# 確保其他模組的 logger 也設定為 DEBUG 級別
logging.getLogger("cleansales_refactor").setLevel(logging.DEBUG)

T = TypeVar("T")

DataReader: TypeAlias = Callable[[], pd.DataFrame]
DataValidator: TypeAlias = Callable[[pd.DataFrame], pd.DataFrame]
DataProcessor: TypeAlias = Callable[[pd.DataFrame], ProcessingResult[T]]
DataExporter: TypeAlias = Callable[[ProcessingResult[T]], None]



def dataframe_md5(dataframe: pd.DataFrame) -> str:
    return hashlib.md5(dataframe.to_csv(index=False).encode()).hexdigest()


def time_it(func: Callable[..., Any]) -> Callable[..., Any]:
    """計時函數"""

    def wrapper(*args: Any, **kwargs: Any) -> Any:
        time_start = time.time()
        result = func(*args, **kwargs)
        time_end = time.time()
        logger.debug(f"{func.__name__}函數執行時間: {time_end - time_start}")
        return result

    return wrapper


def create_bytes_reader(file_content: bytes) -> DataReader:
    def wrapper() -> pd.DataFrame:
        try:
            return pd.read_excel(io.BytesIO(file_content))
        except Exception as e:
            logger.error(f"讀取 Excel 檔案時發生錯誤: {str(e)}")
            raise ValueError("讀取 Excel 檔案時發生錯誤")

    return time_it(wrapper)


def create_dataframe_validator(dataframe: pd.DataFrame) -> DataValidator:
    """建立資料驗證函數"""
    md5s: set[str] = get_all_md5s()

    def wrapper() -> pd.DataFrame:
        if dataframe.empty:
            raise ValueError("資料為空")

        if dataframe_md5(dataframe) in md5s:
            raise ValueError("資料已經處理過")
        
        return dataframe

    return time_it(wrapper)


def create_excel_reader(
    file_path: str | Path, sheet_name: str = "工作表1"
) -> DataReader:
    """建立 Excel 讀取函數"""

    def read_data() -> pd.DataFrame:
        df = pd.read_excel(file_path, sheet_name=sheet_name)
        return df

    return time_it(read_data)


def create_data_processor(processor: IProcessor[T]) -> DataProcessor[T]:
    """建立資料處理函數"""

    def process_data(df: pd.DataFrame) -> ProcessingResult[T]:
        result = processor.process_data(df)
        return result

    return time_it(process_data)


def create_data_exporter(exporter: IExporter[T]) -> DataExporter[T]:
    """建立資料匯出函數"""

    def export_data(result: ProcessingResult[T]) -> None:
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
    exporter = create_data_exporter(SaleSQLiteExporter(str(db_path)))

    def pipeline() -> None:
        try:
            exporter(processor(reader()))
        except Exception as e:
            logger.error(f"處理銷售資料時發生錯誤: {e}")
            raise

    return pipeline


def create_breeds_data_pipeline(
    input_file: str | Path, db_path: str | Path, sheet_name: str = "工作表1"
) -> Callable[[], None]:
    """建立入雛資料處理管道"""
    reader = create_excel_reader(input_file, sheet_name)
    processor = create_data_processor(BreedsProcessor)
    exporter = create_data_exporter(BreedSQLiteExporter(str(db_path)))

    def pipeline() -> None:
        exporter(processor(reader()))

    return pipeline

from cleansales_refactor.models.shared import SourceData, ProcessorPipelineData
def create_sales_pipeline(source_data: SourceData) -> ProcessorPipelineData[T]:
    db_path = "data.db"
    reader = source_data.dataframe
    processor = lambda df: SalesProcessor.process_data(df)
    exporter = lambda source_data, processed_result: SaleSQLiteExporter(str(db_path)).export_data(source_data, processed_result)

    return ProcessorPipelineData(
            source_data=source_data,
            process_result=processor(reader),
            exporter_result=exporter(source_data, processor(reader)))






def sales_data_service() -> None:
    """銷售資料服務"""
    input_file = "sales_sample.xlsx"
    db_path = "data.db"

    pipeline = create_sales_data_pipeline(input_file, db_path)
    pipeline()


def breeds_data_service() -> None:
    """入雛資料服務"""
    input_file = "breeds_sample.xlsx"
    db_path = "data.db"

    pipeline = create_breeds_data_pipeline(input_file, db_path)
    pipeline()


if __name__ == "__main__":
    sales_data_service()
    breeds_data_service()
