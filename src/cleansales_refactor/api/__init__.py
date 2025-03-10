from typing import Generator

from sqlmodel import Session

from cleansales_refactor import Database, settings

db = Database(settings.DB_PATH)


def get_session() -> Generator[Session, None, None]:
    with db.get_session() as session:
        yield session


def main() -> None:
    import uvicorn

    uvicorn.run(
        "cleansales_refactor.api.app:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        reload_dirs=["src/cleansales_refactor"],
    )


__all__ = ["get_session", "main"]
