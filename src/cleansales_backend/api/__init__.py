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

from cleansales_backend.core import (
    ProcessEvent,
    ProcessExecutor,
    TelegramNotifier,
    core_db,
    get_event_bus,
    settings,
)
from cleansales_backend.processors.breeds_schema import BreedRecordProcessor
from cleansales_backend.processors.feeds_schema import FeedRecordProcessor
from cleansales_backend.processors.sales_schema import SaleRecordProcessor
from cleansales_backend.services.query_service import QueryService

logger = logging.getLogger(__name__)
# 設定根 logger
logging.basicConfig(
    level=settings.LOG_LEVEL,
    format=settings.LOG_FORMAT,
    handlers=[logging.StreamHandler()],
)


_process_executor = ProcessExecutor(
    event_bus=get_event_bus(),
    register_events=[
        ProcessEvent.SALES_PROCESSING_STARTED,
        ProcessEvent.BREEDS_PROCESSING_STARTED,
        ProcessEvent.FEEDS_PROCESSING_STARTED,
    ],
)


_telegram_notifier = TelegramNotifier(
    event_bus=get_event_bus(),
    register_events=[
        ProcessEvent.SALES_PROCESSING_COMPLETED,
        ProcessEvent.SALES_PROCESSING_FAILED,
        ProcessEvent.BREEDS_PROCESSING_COMPLETED,
        ProcessEvent.BREEDS_PROCESSING_FAILED,
        ProcessEvent.FEEDS_PROCESSING_COMPLETED,
        ProcessEvent.FEEDS_PROCESSING_FAILED,
    ],
)


_breed_repository = BreedRecordProcessor()
_sale_repository = SaleRecordProcessor()
_feed_repository = FeedRecordProcessor()
_query_service = QueryService(
    _breed_repository,
    _sale_repository,
    _feed_repository,
    core_db,
    get_event_bus(),
)


def get_query_service() -> QueryService:
    """依賴注入：獲取查詢服務實例

    Returns:
        QueryService: 查詢服務實例
    """
    return _query_service


__all__ = ["core_db", "get_event_bus", "ProcessEvent", "get_query_service"]
