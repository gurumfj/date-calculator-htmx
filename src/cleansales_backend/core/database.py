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
from typing import Literal, Protocol

from sqlalchemy import Engine, text
from sqlmodel import Session, SQLModel, create_engine

from cleansales_backend.core.config import get_settings
from cleansales_backend.processors import BreedRecordORM, FeedRecordORM, SaleRecordORM
from cleansales_backend.processors.interface.processors_interface import IORMModel

# from .db_optimizations import setup_db_optimizations

# 註冊所有的 ORM 模型
_orm_models: list[type[IORMModel]] = [BreedRecordORM, SaleRecordORM, FeedRecordORM]

logger = logging.getLogger(__name__)


class DatabaseSettings(Protocol):
    DB: Literal["sqlite", "supabase"]
    DB_ECHO: bool
    SQLITE_DB_PATH: Path
    SUPABASE_DB_POOL: bool
    SUPABASE_DB_HOST: str
    SUPABASE_DB_PASSWORD: str
    SUPABASE_DB_USER: str
    SUPABASE_DB_PORT: int
    SUPABASE_DB_NAME: str


class Database:
    _db_settings: DatabaseSettings
    _engine: Engine

    def __init__(self, db_settings: DatabaseSettings) -> None:
        try:
            self._db_settings = db_settings
            if db_settings.DB == "sqlite":
                self._engine = self.create_sqlite_db()
            elif db_settings.DB == "supabase":
                self._engine = self.create_supabase_db()
            else:
                raise ValueError(f"Invalid DB value: {db_settings.DB}")
        except Exception:
            logger.error("初始化數據庫時發生錯誤")
            raise Exception("初始化數據庫時發生錯誤")
        # finally:
        # 啟動數據庫監控
        # monitor.start_monitoring(self._engine)

    def create_sqlite_db(self) -> Engine:
        """創建 SQLite 數據庫"""
        db_path = Path(self._db_settings.SQLITE_DB_PATH)
        logger.info(f"Creating database at {db_path.absolute()}")
        db_path.parent.mkdir(exist_ok=True)
        logger.info(f"Database created at {db_path.absolute()}")
        engine = create_engine(f"sqlite:///{db_path}")
        with engine.connect() as conn:
            _ = conn.execute(text("PRAGMA foreign_keys=ON"))
            conn.commit()
        SQLModel.metadata.create_all(engine)
        return engine

    def create_supabase_db(self) -> Engine:
        """創建 Supabase 數據庫"""
        try:
            database_url = f"postgresql+psycopg2://{self._db_settings.SUPABASE_DB_USER}:{self._db_settings.SUPABASE_DB_PASSWORD}@{self._db_settings.SUPABASE_DB_HOST}:{self._db_settings.SUPABASE_DB_PORT}/{self._db_settings.SUPABASE_DB_NAME}"
            engine = create_engine(
                database_url,
                pool_pre_ping=self._db_settings.SUPABASE_DB_POOL,
            )
            SQLModel.metadata.create_all(engine)
            logger.info("Supabase 數據庫創建成功")
            return engine
        except Exception as e:
            logger.error(f"創建 Supabase 數據庫時發生錯誤: {e}")
            raise

    def db_health_check(self) -> bool:
        """檢查數據庫連接"""
        try:
            with self._engine.connect() as conn:
                result = conn.execute(text("SELECT 1"))
                return result.scalar() is not None
        except Exception:
            return False

    def get_session(self) -> Generator[Session, None, None]:
        """獲取數據庫會話，用於 FastAPI 依賴注入

        Returns:
            Generator[Session, None, None]: 數據庫會話實例
        """
        session = Session(self._engine)
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    @contextmanager
    def with_session(self) -> Generator[Session, None, None]:
        """
        提供上下文管理器，確保 session 的生命週期管理
        包含重試機制和錯誤恢復

        Yields:
            Session: 數據庫會話實例，可用於執行查詢和修改操作

        Raises:
            Exception: 當資料庫操作失敗時拋出相應異常
        """
        max_retries = 3
        retry_count = 0
        last_error = None

        while retry_count < max_retries:
            try:
                session = Session(self._engine)
                logger.debug("開始數據庫會話")

                try:
                    yield session
                    session.commit()
                    logger.debug("數據庫會話提交成功")
                    return  # 成功完成，直接返回
                except Exception as e:
                    last_error = e
                    session.rollback()
                    retry_info = f"(嘗試 {retry_count + 1}/{max_retries})"
                    error_msg = f"數據庫操作失敗 {retry_info}: {str(e)}"
                    logger.error(error_msg)
                    if retry_count == max_retries - 1:
                        raise last_error  # 拋出最後一個錯誤
                    retry_count += 1
                finally:
                    session.close()
                    logger.debug("數據庫會話結束")
            except Exception as e:
                last_error = e
                retry_info = f"(嘗試 {retry_count + 1}/{max_retries})"
                error_msg = f"創建數據庫會話失敗 {retry_info}: {str(e)}"
                logger.error(error_msg)
                if retry_count == max_retries - 1:
                    raise last_error
                retry_count += 1

        # 如果所有重試都失敗了，拋出最後一個錯誤
        if last_error:
            raise last_error


_core_db: Database | None = None


def get_core_db() -> Database:
    global _core_db
    if _core_db is None:
        _core_db = Database(db_settings=get_settings())
    return _core_db
