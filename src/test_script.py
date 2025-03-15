import argparse
import logging
from pathlib import Path

from cleansales_backend.core.config import settings
from cleansales_backend.core.database import Database
from cleansales_backend.processors.breeds_schema import BreedRecordProcessor
from cleansales_backend.processors.sales_schema import SaleRecordProcessor

logger = logging.getLogger(__name__)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)


# 主程式入口
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Process some integers.")
    # global arguments
    subparsers = parser.add_subparsers(dest="subcommand", required=True)
    import_parser = subparsers.add_parser("import")
    # process_parser = subparsers.add_parser("process")

    import_parser.add_argument(
        "-f", "--file", type=str, required=True, help="Excel file path"
    )
    import_parser.add_argument(
        "type",
        type=str,
        choices=["sales", "breeds"],
        # required=True,
        help="Type of data to process",
    )
    import_parser.add_argument(
        "--no-md5",
        action="store_false",
        dest="check_md5",
        default=True,
        help="Disable MD5 check (default: True)",
    )

    args = parser.parse_args()

    db_path = Path(settings.DB_PATH)
    db = Database(db_path)
    # 測試讀取 Excel 檔案
    file: Path = Path(args.file)
    match args.subcommand:
        case "import":
            match args.type:
                case "sales":
                    with db.get_session() as session:
                        sales_processor = SaleRecordProcessor()
                        logger.info(
                            sales_processor.execute(
                                session, file, check_md5=args.check_md5
                            )
                        )
                case "breeds":
                    with db.get_session() as session:
                        breed_processor = BreedRecordProcessor()
                        logger.info(
                            breed_processor.execute(
                                session, file, check_md5=args.check_md5
                            )
                        )
