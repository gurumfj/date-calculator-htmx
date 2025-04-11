"""
################################################################################
# API 包初始化模組
#
# 這個模組提供了 API 包的初始化配置，包括：
# 1. 數據庫會話管理
# 2. 事件總線配置
# 3. 共享依賴項
#
# 主要功能：
# - 提供數據庫會話依賴
# - 提供事件總線依賴
# - 定義共享的枚舉和常量
################################################################################
"""

import logging
from functools import lru_cache

import httpx
from httpx import AsyncClient
from rich.logging import RichHandler

from cleansales_backend.core import (
    get_core_db,
    get_settings,
)
from cleansales_backend.event_bus.event_bus import get_event_bus
from cleansales_backend.event_bus.executor.process_executor import ProcessExecutor
from cleansales_backend.event_bus.executor.telegram_notifier import TelegramNotifier
from cleansales_backend.processors import RespositoryServiceImpl
from cleansales_backend.services.query_service import QueryService

logger = logging.getLogger(__name__)

logging.basicConfig(
    level=get_settings().LOG_LEVEL,
    handlers=[RichHandler(rich_tracebacks=True, markup=True)],
)

settings = get_settings()
core_db = get_core_db()
# 設定根 logger
logging.basicConfig(
    level=settings.LOG_LEVEL,
    format=settings.LOG_FORMAT,
    handlers=[logging.StreamHandler()],
)


_process_executor = ProcessExecutor(event_bus=get_event_bus())


_telegram_notifier = TelegramNotifier(
    event_bus=get_event_bus(),
    settings=settings,
)

_query_service = QueryService(
    repository_service=RespositoryServiceImpl(),
    db=core_db,
    event_bus=get_event_bus(),
)


def get_query_service() -> QueryService:
    """依賴注入：獲取查詢服務實例

    Returns:
        QueryService: 查詢服務實例
    """
    return _query_service


@lru_cache
def get_client() -> AsyncClient:
    return AsyncClient(
        base_url=settings.SUPABASE_CLIENT_URL,
        timeout=30.0,
        limits=httpx.Limits(max_keepalive_connections=20, max_connections=200),
    )


__all__ = ["core_db", "get_event_bus", "get_query_service", "get_client", "settings"]
