from .config import settings
from .database import Database
from .event_bus import Event, EventBus, TelegramNotifier

core_db = Database(settings.DB_PATH)
_event_bus = EventBus()


def get_event_bus() -> EventBus:
    return _event_bus


__all__ = [
    "Database",
    "settings",
    "TelegramNotifier",
    "Event",
    "get_event_bus",
    "core_db",
]
