import argparse
import logging
from pathlib import Path
from typing import Any

import pandas as pd

from cleansales_backend import Database
from cleansales_backend.core import settings
from cleansales_backend.processors import BreedRecordProcessor, SaleRecordProcessor
from cleansales_backend.services import QueryService
from cleansales_backend.shared.models import SourceData

# 設定根 logger
logging.basicConfig(
    level=settings.LOG_LEVEL,
    format=settings.LOG_FORMAT,
    handlers=[logging.StreamHandler()],
)

logger = logging.getLogger(__name__)

# 確保其他模組的 logger 也設定為 DEBUG 級別
# logging.getLogger("cleansales_backend").setLevel(settings.LOG_LEVEL)


def create_parser() -> argparse.ArgumentParser:
    cli_structure: dict[Any, Any] = {
        "description": "清理銷售和品種資料的命令列工具",
        "global_args": {
            "-db": {
                "dest": "db_path",
                "type": Path,
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
                "args": {
                    "-b": {
                        "dest": "breed",
                        "type": str,
                        "help": "要查詢的品種類型 (預設: 全部)",
                    },
                    "-n": {
                        "dest": "batch_name",
                        "type": str,
                        "help": "要查詢的批次名稱",
                    },
                    "-s": {
                        "dest": "status",
                        "nargs": "+",
                        "choices": ["all", "completed", "breeding", "sale"],
                        "default": ["all"],
                        "help": "要查詢的批次狀態，可指定多個 (預設: all)",
                    },
                    "-t": {
                        "dest": "type",
                        "choices": ["sales", "breeds"],
                        "default": "breeds",
                        "help": "要查詢的資料類型 (預設: 品種資料)",
                    },
                },
            },
        },
    }

    parser = argparse.ArgumentParser(description=cli_structure.get("description", ""))

    # 加入全域參數
    for arg_name, arg_config in cli_structure.get("global_args", {}).items():
        parser.add_argument(arg_name, **arg_config)

    subparsers = parser.add_subparsers(dest="subcommand", required=True)

    # 建立主要命令
    for cmd_name, cmd_config in cli_structure["commands"].items():
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
    1. python -m cleansales_backend
    2. uv run cleansales
    3. 從其他程式中導入：from cleansales_backend import main
    """
    args = parse_args()
    if _db := args.db_path:
        db = Database(_db)
    else:
        db = Database(settings.DB_PATH)
    breed_processor = BreedRecordProcessor()
    sale_processor = SaleRecordProcessor()
    query_service = QueryService(breed_processor, sale_processor)

    try:
        if args.subcommand == "import":
            match args.type:
                case "sales":
                    source_data = SourceData(
                        file_name=str(args.input_file),
                        dataframe=pd.read_excel(args.input_file),
                    )
                    with db.get_session() as session:
                        print(
                            sale_processor.execute(
                                session, source_data, check_md5=args.check_md5
                            ).message
                        )
                case "breeds":
                    source_data = SourceData(
                        file_name=str(args.input_file),
                        dataframe=pd.read_excel(args.input_file),
                    )
                    with db.get_session() as session:
                        print(
                            breed_processor.execute(
                                session, source_data, check_md5=args.check_md5
                            ).message
                        )
                case _:
                    pass
        elif args.subcommand == "query":
            with db.get_session() as session:
                filtered_aggrs = query_service.get_filtered_aggregates(
                    session,
                    batch_name=args.batch_name,
                    breed_type=args.breed,
                    status=args.status,
                )
                if not filtered_aggrs:
                    print("找不到符合條件的批次")
                    return
                msg = ["批次彙整資料"]
                msg.append("=" * 88)
                for aggr in filtered_aggrs:
                    msg.append(str(aggr))
                    if aggr.sales:
                        msg.append("-" * 40)
                        msg.append(str(aggr.sales_trend_data))
                    msg.append("-" * 60)

                msg.append("=" * 88)
                msg.append(f"共 {len(filtered_aggrs)} 筆記錄")
                print("\n".join(msg))

    except Exception as e:
        logger.error(f"處理資料時發生錯誤: {str(e)}")
        raise


if __name__ == "__main__":
    main()

__all__ = ["main"]
