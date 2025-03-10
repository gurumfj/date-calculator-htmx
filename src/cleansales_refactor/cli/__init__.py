import argparse
import logging

from cleansales_refactor.core import settings

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


def create_parser() -> argparse.ArgumentParser:
    CLI_STRUCTURE = {
        "description": "清理銷售和品種資料的命令列工具",
        "global_args": {
            "-db": {
                "dest": "db_path",
                "default": settings.DB_PATH,
                "help": f"資料庫檔案路徑 (預設: {settings.DB_PATH})",
            },
        },
        "commands": {
            "import": {
                "help": "匯入資料",
                "args": {
                    "type": {
                        "choices": ["sales", "breeds"],
                        "help": "要處理的資料類型: sales (銷售資料) 或 breeds (品種資料)",
                    },
                    "-i": {
                        "dest": "input_file",
                        "required": True,
                        "help": "輸入的 Excel 檔案路徑",
                    },
                    "--no-md5": {
                        "action": "store_false",
                        "dest": "check_md5",
                        "help": "關閉 MD5 檢查",
                    },
                },
            },
            "query": {
                "help": "查詢資料",
                "subcommands": {
                    "sales": {
                        "help": "查詢銷售資料",
                        "args": {
                            "-l": {
                                "dest": "limit",
                                "type": int,
                                "default": 100,
                                "help": "要查詢的資料筆數 (預設: 100，最大: 300)",
                            },
                            "-o": {
                                "dest": "offset",
                                "type": int,
                                "default": 0,
                                "help": "要跳過的資料筆數 (預設: 0)",
                            },
                        },
                    },
                    "breeds": {
                        "help": "查詢品種資料",
                        "args": {
                            "-breed": {
                                "type": str,
                                "default": "all",
                                "help": "要查詢的品種類型 (預設: 全部)",
                            },
                            "-n": {
                                "dest": "batch_name",
                                "type": str,
                                "help": "要查詢的批次名稱",
                            },
                            "-s": {
                                "dest": "status",
                                "choices": ["all", "completed", "breeding", "sale"],
                                "default": "all",
                                "help": "要查詢的批次狀態 (預設: 全部)",
                            },
                        },
                    },
                },
            },
        },
    }

    parser = argparse.ArgumentParser(description=CLI_STRUCTURE["description"])

    # 加入全域參數
    for arg_name, arg_config in CLI_STRUCTURE.get("global_args", {}).items():
        parser.add_argument(arg_name, **arg_config)

    subparsers = parser.add_subparsers(dest="subcommand", required=True)

    # 建立主要命令
    for cmd_name, cmd_config in CLI_STRUCTURE["commands"].items():
        cmd_parser = subparsers.add_parser(cmd_name, help=cmd_config["help"])

        # 處理子命令
        if "subcommands" in cmd_config:
            cmd_subparsers = cmd_parser.add_subparsers(dest="query_type", required=True)
            for subcmd_name, subcmd_config in cmd_config["subcommands"].items():
                subcmd_parser = cmd_subparsers.add_parser(
                    subcmd_name, help=subcmd_config["help"]
                )
                # 加入子命令的參數
                for arg_name, arg_config in subcmd_config["args"].items():
                    subcmd_parser.add_argument(arg_name, **arg_config)

        # 處理命令的參數
        if "args" in cmd_config:
            for arg_name, arg_config in cmd_config["args"].items():
                cmd_parser.add_argument(arg_name, **arg_config)

    return parser


def parse_args() -> argparse.Namespace:
    return create_parser().parse_args()


def main() -> None:
    """
    主程式入口點。可以通過以下方式執行：
    1. python -m cleansales_refactor
    2. uv run cleansales
    3. 從其他程式中導入：from cleansales_refactor import main
    """
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
            match args.query_type:
                case "sales":
                    result = cli_service.query_sales(
                        limit=args.limit, offset=args.offset
                    )
                case "breeds":
                    if args.batch_name:
                        result = cli_service.query_breed_by_batch_name(
                            args.batch_name, args.status
                        )
                    else:
                        result = cli_service.query_breeds_not_completed(args.breed)

        print(result)
    except Exception as e:
        logger.error(f"處理資料時發生錯誤: {str(e)}")
        raise


if __name__ == "__main__":
    main()

__all__ = ["main"]
