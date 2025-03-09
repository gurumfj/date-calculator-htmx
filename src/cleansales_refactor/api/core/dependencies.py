from typing import Generator

from fastapi import Depends
from sqlmodel import Session

from cleansales_refactor import Database
from cleansales_refactor.core.config import settings

from ..dependencies.api_dependency import PostApiDependency

db = Database(settings.DB_PATH)


def get_session() -> Generator[Session, None, None]:
    with db.get_session() as session:
        yield session


def get_api_dependency(
    session: Session = Depends(get_session),
) -> PostApiDependency:
    return PostApiDependency(session=session)
