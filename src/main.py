import pandas as pd

# from cleansales_refactor.exporters import ExcelExporter
from cleansales_refactor.exporters.sqlite_exporter import SQLiteExporter
from cleansales_refactor.services import SaleRecordRawDataImporter


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


if __name__ == "__main__":
    main()
