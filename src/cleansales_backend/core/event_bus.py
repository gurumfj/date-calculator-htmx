"""
################################################################################
# 事件總線模組
#
# 這個模組提供了事件驅動架構的核心功能，包括：
# 1. 事件定義和管理
# 2. 事件發布和訂閱
# 3. 通知處理
#
# 主要功能：
# - 事件總線實現
# - 事件處理器註冊
# - Telegram 通知集成
################################################################################
"""

import logging
import threading
from collections import defaultdict
from dataclasses import dataclass
from enum import Enum
from typing import Any, Callable

logger = logging.getLogger(__name__)


@dataclass
class Event:
    """事件數據類"""

    event: Enum
    message: str
    content: dict[str, Any]


class EventBus:
    """事件總線類"""

    __instance: "EventBus | None" = None
    _initialized: bool = False

    def __new__(cls) -> "EventBus":
        if cls.__instance is None:
            cls.__instance = super().__new__(cls)
        return cls.__instance

    def __init__(self) -> None:
        if not self._initialized:
            self._initialized = True
            self.callbacks: dict[Enum, list[Callable[[Event], None]]] = defaultdict(
                list
            )

    def publish(self, event: Event) -> None:
        """發布事件

        Args:
            event (Event): 要發布的事件
        """
        for callback in self.callbacks[event.event]:
            threading.Thread(target=callback, args=(event,), daemon=True).start()

    def register(self, event: Enum, callback: Callable[[Event], None]) -> None:
        """註冊事件處理器

        Args:
            event (Enum): 事件類型
            callback (Callable[[Event], None]): 事件處理器
        """
        self.callbacks.setdefault(event, []).append(callback)
