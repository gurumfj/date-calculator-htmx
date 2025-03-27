"""
################################################################################
# 核心模組初始化
#
# 這個模組提供了系統核心組件的初始化和導出，包括：
# 1. 配置管理
# 2. 數據庫連接
# 3. 事件總線
# 4. 處理器執行器
# 5. 通知處理器
################################################################################
"""

from .config import settings
from .database import Database
from .event_bus import Event, EventBus
from .events import ProcessEvent
from .process_executor import ProcessExecutor
from .telegram_notifier import TelegramNotifier

# 創建核心數據庫實例和事件總線實例
core_db = Database(settings.DB_PATH)
_event_bus = EventBus()


def get_event_bus() -> EventBus:
    return _event_bus


__all__ = [
    "settings",
    "Database",
    "ProcessExecutor",
    "Event",
    "EventBus",
    "TelegramNotifier",
    "ProcessEvent",
    "core_db",
    "get_event_bus",
]
