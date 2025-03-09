import argparse
import logging

from cleansales_refactor.core import Database, settings
from cleansales_refactor.services import CleanSalesService, QueryService

from .cli_service import CLIService

# 設定根 logger
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)

logger = logging.getLogger(__name__)

# 確保其他模組的 logger 也設定為 DEBUG 級別
logging.getLogger("cleansales_refactor").setLevel(logging.DEBUG)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="清理銷售和品種資料的命令列工具")

    subparsers = parser.add_subparsers(dest="subcommand", required=True)

    """ import """
    import_parser = subparsers.add_parser("import", help="匯入資料")
    import_parser.add_argument(
        "type",
        choices=["sales", "breeds"],
        help="要處理的資料類型: sales (銷售資料) 或 breeds (品種資料)",
    )
    import_parser.add_argument(
        "-i",
        type=str,
        required=True,
        dest="input_file",
        help="輸入的 Excel 檔案路徑",
    )
    import_parser.add_argument(
        "-o",
        type=str,
        default=settings.DB_PATH,
        dest="db_path",
        help=f"資料庫檔案路徑 (預設: {settings.DB_PATH})",
    )
    import_parser.add_argument(
        "--no-md5",
        action="store_false",
        dest="check_md5",
        help="關閉 MD5 檢查",
    )

    """ query """
    query_parser = subparsers.add_parser("query", help="查詢資料")
    query_parser.add_argument(
        "-db",
        "--db-path",
        type=str,
        default=settings.DB_PATH,
        dest="db_path",
        help=f"資料庫檔案路徑 (預設: {settings.DB_PATH})",
    )
    query_parser.add_argument(
        "type",
        choices=["sales", "breeds"],
        help="要查詢的資料類型: sales (銷售資料) 或 breeds (品種資料)",
    )
    query_parser.add_argument(
        "-breed",
        type=str,
        default="all",
        help="要查詢的品種類型 (預設: 全部)",
    )
    return parser.parse_args()


def main() -> None:
    """
    主程式入口點。可以通過以下方式執行：
    1. python -m cleansales_refactor
    2. uv run cleansales
    3. 從其他程式中導入：from cleansales_refactor import main
    """

    """ initialize """
    args = parse_args()
    cli_service = CLIService(args.db_path)
    try:
        if args.subcommand == "import":
            match args.type:
                case "sales":
                    result = cli_service.import_sales(
                        args.input_file, check_md5=args.check_md5
                    )
                case "breeds":
                    result = cli_service.import_breeds(
                        args.input_file, check_md5=args.check_md5
                    )
        elif args.subcommand == "query":
            match args.type:
                case "sales":
                    result = "command is not implemented"
                case "breeds":
                    result = cli_service.query_breeds(args.breed)

        print(result)
    except Exception as e:
        logger.error(f"處理資料時發生錯誤: {str(e)}")
        raise


if __name__ == "__main__":
    main()
