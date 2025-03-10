from typing import Generator

from sqlmodel import Session

from cleansales_refactor import Database, settings

db = Database(settings.DB_PATH)


def get_session() -> Generator[Session, None, None]:
    with db.get_session() as session:
        yield session


__all__ = ["get_session"]
