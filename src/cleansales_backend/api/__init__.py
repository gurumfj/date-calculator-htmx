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
from collections.abc import Generator
from enum import Enum

from sqlmodel import Session

from cleansales_backend.core import Database, EventBus, TelegramNotifier, settings

logger = logging.getLogger(__name__)
# 設定根 logger
logging.basicConfig(
    level=settings.LOG_LEVEL,
    format=settings.LOG_FORMAT,
    handlers=[logging.StreamHandler()],
)


db = Database(settings.DB_PATH)


def get_session() -> Generator[Session, None, None]:
    """獲取數據庫會話

    Yields:
        Generator[Session, None, None]: 數據庫會話生成器
    """
    with db.get_session() as session:
        yield session


_event_bus = EventBus()


def get_event_bus() -> EventBus:
    """獲取事件總線實例

    Returns:
        EventBus: 事件總線實例
    """
    return _event_bus


class ProcessEvent(str, Enum):
    """處理事件枚舉"""

    SALES_PROCESSING_STARTED = "販售資料上傳開始"
    SALES_PROCESSING_COMPLETED = "販售資料上傳完成"
    SALES_PROCESSING_FAILED = "販售資料上傳失敗"
    BREEDS_PROCESSING_STARTED = "入雛資料上傳開始"
    BREEDS_PROCESSING_COMPLETED = "入雛資料上傳完成"
    BREEDS_PROCESSING_FAILED = "入雛資料上傳失敗"


_telegram_notifier = TelegramNotifier(
    event_bus=get_event_bus(),
    register_events=[
        ProcessEvent.SALES_PROCESSING_COMPLETED,
        ProcessEvent.SALES_PROCESSING_FAILED,
        ProcessEvent.BREEDS_PROCESSING_COMPLETED,
        ProcessEvent.BREEDS_PROCESSING_FAILED,
    ],
)


def main() -> None:
    """API 服務入口點"""
    import uvicorn

    uvicorn.run(
        "cleansales_backend.api.app:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.API_RELOAD,
        reload_dirs=["src/cleansales_backend"],
    )


__all__ = ["get_session", "main", "get_event_bus", "ProcessEvent"]
