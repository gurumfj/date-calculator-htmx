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

from sqlalchemy import Engine, text
from sqlmodel import Session, SQLModel, create_engine

from cleansales_backend.processors import BreedRecordORM, FeedRecordORM, SaleRecordORM
from cleansales_backend.processors.interface.processors_interface import IORMModel

from .config import settings
from .db_monitor import monitor

# from .db_optimizations import setup_db_optimizations

# 註冊所有的 ORM 模型
_orm_models: list[type[IORMModel]] = [BreedRecordORM, SaleRecordORM, FeedRecordORM]

logger = logging.getLogger(__name__)


class Database:
    _engine: Engine

    def __init__(self, sqlite_db_path: Path | str | None = None) -> None:
        try:
            self._engine = (
                self.create_supabase_db()
                if settings.FEATURES_SUPABASE
                else self.create_sqlite_db(sqlite_db_path)
            )
        except Exception:
            logger.error("初始化數據庫時發生錯誤")
            raise Exception("初始化數據庫時發生錯誤")
        finally:
            # 啟動數據庫監控
            monitor.start_monitoring(self._engine)

    def get_db_state(self) -> str:
        """獲取數據庫狀態"""
        return "Supabase" if settings.FEATURES_SUPABASE else "SQLite"

    def create_sqlite_db(self, sqlite_db_path: Path | str | None = None) -> Engine:
        """創建 SQLite 數據庫"""
        db_path = (
            Path(sqlite_db_path) if sqlite_db_path else Path(settings.SQLITE_DB_PATH)
        )
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
            database_url = f"postgresql+psycopg2://{settings.SUPABASE_DB_USER}:{settings.SUPABASE_DB_PASSWORD}@{settings.SUPABASE_DB_HOST}:{settings.SUPABASE_DB_PORT}/{settings.SUPABASE_DB_NAME}"
            engine = create_engine(
                database_url,
                pool_pre_ping=settings.SUPABASE_DB_POOL,
            )
            SQLModel.metadata.create_all(engine)
            logger.info("Supabase 數據庫創建成功")
            with engine.connect() as conn:
                result = conn.execute(text("SELECT 1"))
                print("Supabase 數據庫連接成功") if result.scalar() else print(
                    "Supabase 數據庫連接失敗"
                )
                conn.commit()
            return engine
        except Exception as e:
            logger.error(f"創建 Supabase 數據庫時發生錯誤: {e}")
            raise

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
