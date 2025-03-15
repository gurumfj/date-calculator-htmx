"""
################################################################################
# 數據庫模組
#
# 這個模組提供了數據庫的初始化和管理功能，包括：
# 1. 數據庫引擎創建
# 2. 會話管理
# 3. 數據庫創建
#
# 主要功能：
# - 提供數據庫引擎
# - 提供數據庫會話管理
# - 提供數據庫創建功能
################################################################################
"""

import logging
from collections.abc import Generator
from contextlib import contextmanager
from pathlib import Path

from sqlalchemy import Engine
from sqlmodel import Session, SQLModel, create_engine

from .config import settings

logger = logging.getLogger(__name__)


class Database:
    _engine: Engine
    _db_path: Path

    def __init__(self, db_path: Path | str) -> None:
        self._db_path = Path(db_path) if isinstance(db_path, str) else db_path
        self._db_path.parent.mkdir(exist_ok=True)

        self._engine = create_engine(
            f"sqlite:///{self._db_path}", echo=settings.DB_ECHO
        )
        SQLModel.metadata.create_all(self._engine)
        logger.info(f"Database created at {db_path}")

    @contextmanager
    def get_session(self) -> Generator[Session, None, None]:
        with Session(self._engine) as session:
            try:
                yield session
                session.commit()
            except Exception as e:
                session.rollback()
                raise e
            finally:
                session.close()
