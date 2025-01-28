from sales_records_importer import SaleRecordRawDataImporter
import pandas as pd

def main() -> None:
    input_file = "sales_sample.xlsx"
    output_file = "output.xlsx"
    errors_file = "errors.xlsx"
    importer = SaleRecordRawDataImporter()
    importer.execute(pd.read_excel(input_file, sheet_name="工作表1"))
    importer.to_excel(output_file)
    importer.errors_to_excel(errors_file)

if __name__ == "__main__":
    main()
