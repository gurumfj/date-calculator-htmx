import argparse
import logging

from cleansales_refactor import DataService

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
    parser.add_argument(
        "--db-path",
        type=str,
        default="data/main.db",
        help="資料庫檔案路徑 (預設: data/main.db)",
    )
    parser.add_argument(
        "--type",
        type=str,
        choices=["sales", "breeds"],
        required=True,
        help="要處理的資料類型: sales (銷售資料) 或 breeds (品種資料)",
    )
    parser.add_argument(
        "--input-file", type=str, required=True, help="輸入的 Excel 檔案路徑"
    )
    parser.add_argument(
        "--check-md5",
        action="store_true",
        default=True,
        help="是否檢查 MD5 避免重複匯入 (預設: True)",
    )
    parser.add_argument(
        "--no-check-md5",
        action="store_false",
        dest="check_md5",
        help="關閉 MD5 檢查",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    data_service = DataService(args.db_path)

    try:
        if args.type == "sales":
            result = data_service.sales_data_service(
                args.input_file, check_md5=args.check_md5
            )
        else:  # breeds
            result = data_service.breeds_data_service(
                args.input_file, check_md5=args.check_md5
            )
        print(result)
    except Exception as e:
        logger.error(f"處理資料時發生錯誤: {str(e)}")
        raise


if __name__ == "__main__":
    main()
