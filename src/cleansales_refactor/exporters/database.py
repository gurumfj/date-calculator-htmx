from sqlmodel import Session, SQLModel, create_engine

class Database:
    def __init__(self, db_path: str) -> None:
        self.db_path = db_path
        self.engine = create_engine(f"sqlite:///{db_path}", echo=False)
        SQLModel.metadata.create_all(self.engine)

    def get_session(self) -> Session:
        return Session(self.engine)
