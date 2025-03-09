from typing import Generator

from fastapi import Depends
from sqlmodel import Session

from src.cleansales_refactor import Database
from src.core.event_bus import EventBus

from ..dependencies.api_dependency import PostApiDependency


def get_event_bus() -> EventBus:
    return EventBus()


db = Database("data/cleansales.db")


def get_session() -> Generator[Session, None, None]:
    with db.get_session() as session:
        yield session


def get_api_dependency(
    event_bus: EventBus = Depends(get_event_bus),
    session: Session = Depends(get_session),
) -> PostApiDependency:
    return PostApiDependency(event_bus=event_bus, session=session)
