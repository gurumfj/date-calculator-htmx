import pandas as pd

# from cleansales_refactor.exporters import ExcelExporter
from cleansales_refactor.exporters.sqlite_exporter import SQLiteExporter
from cleansales_refactor.services import SaleRecordRawDataImporter
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

def main() -> None:
    input_file = "sales_sample.xlsx"
    # output_file = "output.xlsx"
    # errors_file = "errors.xlsx"
    db_path = "sales_data.db"
    exporter = SQLiteExporter(db_path)
    importer = SaleRecordRawDataImporter(exporter)
    importer.execute(pd.read_excel(input_file, sheet_name="工作表1"))
    importer.export_data()
    importer.export_errors()

def test_processor_process_data2() -> None:
    import time
    from cleansales_refactor.processor.sale_record_processor import SalesProcessor
    input_file = "sales_sample.xlsx"
    data = pd.read_excel(input_file, sheet_name="工作表1")
    start_time = time.time()
    result = SalesProcessor.process_data(data)
    end_time = time.time()
    print(f"Time taken: {end_time - start_time} seconds")
    exporter = SQLiteExporter("sales_data.db")
    exporter.export_data(result)
    exporter.export_errors(result)
if __name__ == "__main__":
    test_processor_process_data2()
    # main()
