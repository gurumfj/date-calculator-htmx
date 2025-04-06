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
from enum import Enum
from functools import lru_cache
from typing import Any, Callable

from typing_extensions import Protocol

logger = logging.getLogger(__name__)


class IEventPayload(Protocol):
    event: Enum
    content: Any


class EventBus:
    """事件總線類

    Do not create EventBus instance directly, use get_event_bus() instead
    """

    def __init__(self) -> None:
        self.callbacks: dict[Enum, list[Callable[[Any], None]]] = defaultdict(list)

    def publish(self, payload: IEventPayload) -> None:
        """發布事件

        Args:
            payload (IEventPayload): 事件內容
        """
        for callback in self.callbacks[payload.event]:
            threading.Thread(target=callback, args=(payload,), daemon=False).start()
            logger.debug(f"Published event: {payload}")

    def register(self, event_type: Enum, callback: Callable[[Any], None]) -> None:
        """註冊事件處理器

        Args:
            event_type (Enum): 事件類型
            callback (Callable[[Any], None]): 事件處理器
        """
        self.callbacks.setdefault(event_type, []).append(callback)
        logger.debug(f"Registered callback for event: {event_type}")


@lru_cache(maxsize=None)
def get_event_bus() -> EventBus:
    logger.info("Creating event bus")
    return EventBus()
