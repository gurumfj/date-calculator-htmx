from contextlib import contextmanager
from sqlmodel import Session, SQLModel, create_engine
from typing import Generator, Callable, Any

class Database:
    def __init__(self, db_path: str) -> None:
        self.db_path = db_path
        self.engine = create_engine(f"sqlite:///{db_path}", echo=False)
        SQLModel.metadata.create_all(self.engine)


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


    def session(self, callback: Callable[[Session, Any], Any]) -> Callable[[Any], Any]:
        """
        使用 session 的 callback 函數
        """
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            try:
                with self.get_session() as session:
                    return callback(session, *args, **kwargs)
            except Exception as e:
                session.rollback()
                raise e
            finally:
                session.close()
        return wrapper
