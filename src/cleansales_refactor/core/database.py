import logging
from contextlib import contextmanager
from typing import Generator

from sqlmodel import Session, SQLModel, create_engine

logger = logging.getLogger(__name__)


class Database:
    def __init__(self, db_path: str) -> None:
        self.engine = create_engine(f"sqlite:///{db_path}", echo=False)
        SQLModel.metadata.create_all(self.engine)
        logger.info(f"Database created at {db_path}")

    @contextmanager
    def get_session(self) -> Generator[Session, None, None]:
        with Session(self.engine) as session:
            try:
                yield session
                session.commit()
            except Exception as e:
                session.rollback()
                raise e
            finally:
                session.close()
