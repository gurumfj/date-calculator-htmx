from typing import Generator

from sqlmodel import Session

from cleansales_refactor import Database

# 初始化資料庫
db = Database("data/cleansales.db")


def get_session() -> Generator[Session, None, None]:
    """獲取資料庫會話的依賴注入函數"""
    with db.get_session() as session:
        yield session
