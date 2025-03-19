"""
################################################################################
# 數據庫監控模組
#
# 這個模組提供了數據庫性能監控功能，包括：
# 1. 查詢執行時間統計
# 2. 連接池狀態監控
# 3. 慢查詢日誌
################################################################################
"""

import logging
import time
from collections.abc import Callable
from functools import wraps
from typing import Any

from sqlalchemy import event
from sqlalchemy.engine import Engine

logger = logging.getLogger(__name__)


class DBMonitor:
    def __init__(self) -> None:
        self.slow_query_threshold: float = 0.5  # 慢查詢閾值（秒）
        self.query_stats: dict[str, dict[str, float]] = {}

    def start_monitoring(self, engine: Engine) -> None:
        @event.listens_for(engine, "before_cursor_execute")
        def before_cursor_execute(
            conn: Any,
            cursor: Any,
            statement: str,
            parameters: Any,
            context: Any,
            executemany: bool,
        ) -> None:
            conn.info.setdefault("query_start_time", []).append(time.time())

        @event.listens_for(engine, "after_cursor_execute")
        def after_cursor_execute(
            conn: Any,
            cursor: Any,
            statement: str,
            parameters: Any,
            context: Any,
            executemany: bool,
        ) -> None:
            total_time = time.time() - conn.info["query_start_time"].pop()

            # 記錄慢查詢
            if total_time > self.slow_query_threshold:
                logger.warning(f"慢查詢檢測 ({total_time:.2f}s): {statement}")

            # 更新查詢統計
            if statement in self.query_stats:
                stats = self.query_stats[statement]
                stats["count"] += 1
                stats["total_time"] += total_time
                stats["avg_time"] = stats["total_time"] / stats["count"]
            else:
                self.query_stats[statement] = {
                    "count": 1,
                    "total_time": total_time,
                    "avg_time": total_time,
                }


def log_execution_time(func: Callable[..., Any]) -> Callable[..., Any]:
    """函數執行時間裝飾器"""

    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()

        execution_time = end_time - start_time
        logger.info(f"{func.__name__} 執行時間: {execution_time:.2f}秒")

        return result

    return wrapper


# 創建全局監控實例
monitor = DBMonitor()
