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

from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable

import requests
from pydantic import AnyHttpUrl

from .config import settings


@dataclass
class Event:
    """事件數據類"""

    event: Enum
    content: dict[str, Any]
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.metadata["timestamp"] = datetime.now()


class EventBus:
    """事件總線類"""

    __instance = None

    def __new__(cls) -> "EventBus":
        if cls.__instance is None:
            cls.__instance = super().__new__(cls)
        return cls.__instance

    def __init__(self) -> None:
        if not hasattr(self, "_initialized"):
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
            callback(event)

    def register(self, event: Enum, callback: Callable[[Event], None]) -> None:
        """註冊事件處理器

        Args:
            event (Enum): 事件類型
            callback (Callable[[Event], None]): 事件處理器
        """
        self.callbacks.setdefault(event, []).append(callback)


class TelegramNotifier:
    """Telegram 通知處理器"""

    post_url: AnyHttpUrl | None = None

    def __init__(self, event_bus: EventBus, register_events: list[Enum]) -> None:
        """初始化 Telegram 通知處理器

        Args:
            event_bus (EventBus): 事件總線實例
            register_events (list[Enum]): 要註冊的事件列表
        """
        self._event_bus = event_bus
        self.post_url = settings.TELEGRAM_WEBHOOK_URL
        # 只有在配置了 Telegram 時才註冊事件處理器
        if self.post_url:
            for event in register_events:
                self._event_bus.register(event, self.notify)

    def notify(self, event: Event) -> None:
        """發送 Telegram 通知

        Args:
            event (Event): 要發送的事件
        """
        try:
            if not self.post_url:
                return
            request = requests.post(
                url=self.post_url.unicode_string(),
                json=event.content,
            )
            print(request)
        except Exception as e:
            print(e)
