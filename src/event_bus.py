import os
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable

import requests


@dataclass
class Event:
    event: Enum
    content: dict[str, Any]
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.metadata["timestamp"] = datetime.now()


class EventBus:
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

    @classmethod
    def get_instance(cls) -> "EventBus":
        if cls.__instance is None:
            if cls.__instance is None:
                cls.__instance = cls()
        return cls.__instance

    def publish(self, event: Event) -> None:
        for callback in self.callbacks[event.event]:
            callback(event)

    def register(self, event: Enum, callback: Callable[[Event], None]) -> None:
        self.callbacks.setdefault(event, []).append(callback)


class TelegramNotifier:
    post_url: str | None = None

    def __init__(self, event_bus: EventBus, register_events: list[Enum]) -> None:
        self.event_bus = event_bus
        self.post_url = os.getenv("TELEGRAM_WEBHOOK_URL")
        if not self.post_url:
            raise ValueError("TELEGRAM_WEBHOOK_URL is not set")
        for event in register_events:
            self.event_bus.register(event, self.notify)

    def notify(self, event: Event) -> None:
        try:
            if not self.post_url:
                raise ValueError("TELEGRAM_WEBHOOK_URL is not set")
            request = requests.post(
                url=self.post_url,
                json=event.content,
            )
            print(request)
        except Exception as e:
            print(e)
