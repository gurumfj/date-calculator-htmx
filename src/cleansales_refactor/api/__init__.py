from enum import Enum
from typing import Generator

from sqlmodel import Session

from cleansales_refactor import Database, settings
from cleansales_refactor.core import EventBus, TelegramNotifier

db = Database(settings.DB_PATH)


def get_session() -> Generator[Session, None, None]:
    with db.get_session() as session:
        yield session


_event_bus = EventBus()


def get_event_bus() -> EventBus:
    return _event_bus


class ProcessEvent(Enum):
    SALES_PROCESSING_COMPLETED = "sales_processing_completed"
    SALES_PROCESSING_FAILED = "sales_processing_failed"

    BREEDS_PROCESSING_COMPLETED = "breeds_processing_completed"
    BREEDS_PROCESSING_FAILED = "breeds_processing_failed"


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
    import uvicorn

    uvicorn.run(
        "cleansales_refactor.api.app:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        reload_dirs=["src/cleansales_refactor"],
    )


__all__ = ["get_session", "main", "get_event_bus", "ProcessEvent"]
