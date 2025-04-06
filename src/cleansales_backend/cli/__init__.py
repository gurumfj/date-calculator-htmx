import argparse
import logging
from pathlib import Path
from typing import Any

import pandas as pd
from rich.logging import RichHandler

from cleansales_backend.core.config import get_settings
from cleansales_backend.core.database import Database
from cleansales_backend.domain.models.batch_state import BatchState
from cleansales_backend.event_bus import EventBus
from cleansales_backend.processors import RespositoryServiceImpl
from cleansales_backend.processors.breeds_schema import BreedRecordProcessor
from cleansales_backend.processors.sales_schema import SaleRecordProcessor
from cleansales_backend.services import QueryService
from cleansales_backend.shared.models import SourceData

settings = get_settings()

# 設定根 logger
logging.basicConfig(
    level=settings.LOG_LEVEL,
    format=settings.LOG_FORMAT,
    handlers=[RichHandler(rich_tracebacks=True, markup=True)],
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
                "help": f"資料庫檔案路徑 (預設: {settings.SQLITE_DB_PATH})",
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
                    "--force": {
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
                        "choices": ["黑羽", "古早", "舍黑", "閹雞"],
                        "action": "append",
                        "default": None,
                        "help": "要查詢的品種類型 (預設: 全部)",
                    },
                    "-n": {
                        "dest": "name",
                        "type": str,
                        "default": None,
                        "help": "要查詢的批次名稱",
                    },
                    "-s": {
                        "dest": "status",
                        "action": "append",
                        "choices": ["completed", "breeding", "sale"],
                        "default": None,
                        "help": "要查詢的批次狀態，可指定多個",
                    },
                    "-o": {
                        "dest": "output",
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
        _ = parser.add_argument(arg_name, **arg_config)

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
                    _ = subcmd_parser.add_argument(arg_name, **arg_config)

        # 處理命令的參數
        if "args" in cmd_config:
            for arg_name, arg_config in cmd_config["args"].items():
                _ = cmd_parser.add_argument(arg_name, **arg_config)

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
    _db = Database(settings)

    sales_repository = SaleRecordProcessor()
    breeds_repository = BreedRecordProcessor()
    # feeds_repository = FeedRecordProcessor()

    query_service = QueryService(
        repository_service=RespositoryServiceImpl(), db=_db, event_bus=EventBus()
    )

    try:
        if args.subcommand == "import":
            match args.type:
                case "sales":
                    source_data = SourceData(
                        file_name=str(args.input_file),
                        dataframe=pd.read_excel(args.input_file),
                    )
                    with _db.with_session() as session:
                        _ = sales_repository.execute(
                            session,
                            source_data,
                            check_md5=args.check_md5,
                        )
                        query_service.cache_clear()
                        print("OK")
                case "breeds":
                    source_data = SourceData(
                        file_name=str(args.input_file),
                        dataframe=pd.read_excel(args.input_file),
                    )
                    with _db.with_session() as session:
                        _ = breeds_repository.execute(
                            session,
                            source_data,
                            check_md5=args.check_md5,
                        )
                        query_service.cache_clear()
                        print("OK")
                case _:
                    pass
        elif args.subcommand == "query":
            with _db.with_session() as session:
                all_aggrs = query_service.get_batch_aggregates()
            search_name = args.name or None
            search_breed: list[str] = args.breed or [
                "黑羽",
                "古早",
                "舍黑",
                "閹雞",
            ]
            search_status: list[BatchState] = [
                BatchState(status) for status in (args.status) or ["breeding", "sale"]
            ]
            print(f"查詢狀態: {[s.value for s in search_status]}")
            print(f"查詢品種: {search_breed}")
            print(f"查詢批次名稱: {search_name}")
            filtered_aggrs = [
                aggr
                for aggr in all_aggrs
                if (aggr.batch_state in search_status)
                and (
                    search_name is None
                    or (aggr.batch_name and search_name in aggr.batch_name)
                )
                and any(
                    breed in set(r.chicken_breed for r in aggr.batch_records)
                    for breed in search_breed
                )
            ]
            if not filtered_aggrs:
                print("找不到符合條件的批次")
                return
            msg = ["批次彙整資料"]
            msg.append("=" * 88)
            for aggr in filtered_aggrs:
                msg.append(str(aggr))
                if aggr.sales_summary:
                    msg.append("-" * 40)
                    msg.append(str(aggr.sales_summary))
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
