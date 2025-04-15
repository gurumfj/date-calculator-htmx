"""
################################################################################
# 數據庫模組
#
# 這個模組提供了數據庫的初始化和管理功能，包括：
# 1. 數據庫連接工廠和策略
# 2. 會話管理
# 3. 數據庫健康檢查
################################################################################
"""

import logging
import time
from abc import ABC, abstractmethod
from collections.abc import Generator
from contextlib import contextmanager
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any, Callable, Literal, Protocol, TypeVar, override

from sqlalchemy import Engine, text
from sqlmodel import Session, SQLModel, create_engine

from cleansales_backend.core.config import get_settings

# 將模型導入和註冊移至方法內部，避免循環導入

logger = logging.getLogger(__name__)

# 類型定義
T = TypeVar("T")
DbFactory = Callable[[], Engine]


class DatabaseSettings(Protocol):
    """數據庫設置協議"""

    DB: Literal["sqlite", "supabase", "supabase_pooler"]
    DB_ECHO: bool
    SQLITE_DB_PATH: Path
    SUPABASE_DB_HOST: str
    SUPABASE_DB_PASSWORD: str
    SUPABASE_DB_USER: str
    SUPABASE_DB_PORT: int
    SUPABASE_DB_NAME: str
    SUPABASE_POOLER_TENANT_ID: str


class DbConnectionStrategy(ABC):
    """數據庫連接策略抽象類，定義統一接口"""

    @abstractmethod
    def create_engine(self, settings: DatabaseSettings) -> Engine:
        """創建數據庫引擎"""
        pass

    def initialize_tables(self, engine: Engine) -> None:
        """初始化數據表"""
        # 延遲導入 ORM 模型，避免循環依賴
        from cleansales_backend.processors import (
            BreedRecordORM,
            FeedRecordORM,
            SaleRecordORM,
        )
        from cleansales_backend.processors.interface.processors_interface import (
            IORMModel,
        )

        # 註冊所有的 ORM 模型
        _orm_models: list[type[IORMModel]] = [
            BreedRecordORM,
            SaleRecordORM,
            FeedRecordORM,
        ]

        SQLModel.metadata.create_all(engine)


class SqliteConnectionStrategy(DbConnectionStrategy):
    """SQLite 數據庫連接策略"""

    @override
    def create_engine(self, settings: DatabaseSettings) -> Engine:
        """創建 SQLite 數據庫引擎"""
        db_path = Path(settings.SQLITE_DB_PATH)
        logger.info(f"Creating SQLite database at {db_path.absolute()}")
        db_path.parent.mkdir(exist_ok=True)

        engine = create_engine(
            f"sqlite:///{db_path}",
            echo=settings.DB_ECHO,
            connect_args={"check_same_thread": False},
        )

        # 啟用外鍵約束
        with engine.connect() as conn:
            _ = conn.execute(text("PRAGMA foreign_keys=ON"))
            conn.commit()

        self.initialize_tables(engine)
        logger.info(f"SQLite database ready at {db_path.absolute()}")
        return engine


class SupabaseConnectionStrategy(DbConnectionStrategy):
    """Supabase 數據庫連接策略"""

    @override
    def create_engine(self, settings: DatabaseSettings) -> Engine:
        """創建 Supabase 數據庫引擎"""
        logger.info("Creating Supabase database connection")

        database_url = (
            f"postgresql+psycopg2://{settings.SUPABASE_DB_USER}:{settings.SUPABASE_DB_PASSWORD}"
            f"@{settings.SUPABASE_DB_HOST}:{settings.SUPABASE_DB_PORT}"
            f"/{settings.SUPABASE_DB_NAME}"
        )

        engine = create_engine(
            database_url,
            echo=settings.DB_ECHO,
        )

        self.initialize_tables(engine)
        logger.info("Supabase database connection ready")
        return engine


class SupabasePoolerConnectionStrategy(DbConnectionStrategy):
    """Supabase Pooler 連接策略"""

    @override
    def create_engine(self, settings: DatabaseSettings) -> Engine:
        """創建 Supabase Pooler 連接"""
        logger.info("Creating Supabase Pooler connection")

        database_url = (
            f"postgresql+psycopg2://"
            f"{settings.SUPABASE_DB_USER}.{settings.SUPABASE_POOLER_TENANT_ID}"
            f":{settings.SUPABASE_DB_PASSWORD}"
            f"@{settings.SUPABASE_DB_HOST}:{settings.SUPABASE_DB_PORT}"
            f"/{settings.SUPABASE_DB_NAME}"
        )

        engine = create_engine(
            database_url,
            echo=settings.DB_ECHO,
            pool_pre_ping=True,
        )

        self.initialize_tables(engine)
        logger.info("Supabase Pooler connection ready")
        return engine


@dataclass
class DatabaseConnector:
    """數據庫連接器，管理不同數據庫類型的連接策略"""

    settings: DatabaseSettings

    def get_connection_strategy(self) -> DbConnectionStrategy:
        """根據設置選擇合適的連接策略"""
        if self.settings.DB == "sqlite":
            return SqliteConnectionStrategy()
        elif self.settings.DB == "supabase_pooler":
            return SupabasePoolerConnectionStrategy()
        elif self.settings.DB == "supabase":
            return SupabaseConnectionStrategy()
        else:
            raise ValueError(f"不支援的數據庫類型: {self.settings.DB}")

    def create_engine(self) -> Engine:
        """創建數據庫引擎"""
        strategy = self.get_connection_strategy()
        return strategy.create_engine(self.settings)


class Database:
    """數據庫管理類，提供會話管理和健康檢查"""

    def __init__(self, db_settings: DatabaseSettings) -> None:
        """初始化數據庫管理器"""
        try:
            self._db_settings: DatabaseSettings = db_settings
            connector = DatabaseConnector(db_settings)
            self._engine: Engine = connector.create_engine()
        except Exception as e:
            logger.error(f"初始化數據庫時發生錯誤: {e}", exc_info=True)
            raise RuntimeError(f"無法初始化數據庫: {e}") from e

    def db_health_check(self) -> bool:
        """檢查數據庫連接"""
        try:
            with self._engine.connect() as conn:
                result = conn.execute(text("SELECT 1"))
                return result.scalar() is not None
        except Exception as e:
            logger.error(f"數據庫健康檢查失敗: {e}")
            return False

    def get_session(self) -> Generator[Session, None, None]:
        """獲取數據庫會話，用於 FastAPI 依賴注入"""
        session = Session(self._engine)
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"數據庫會話操作失敗: {e}")
            raise
        finally:
            session.close()

    @contextmanager
    def with_session(self) -> Generator[Session, None, None]:
        """
        提供上下文管理器，確保 session 的生命週期管理，包含重試機制和錯誤恢復

        這個上下文管理器可以重複嘗試創建數據庫會話，直到成功或超過最大嘗試次數為止。
        在嘗試創建數據庫會話時，會將錯誤日誌記錄下來，並在最後一個嘗試失敗時拋出最後一個錯誤。

        Yielded session 會在上下文管理器結束時自動 close，無需手動關閉。
        """
        max_retries = 3
        retry_count = 0
        last_error = None

        while retry_count < max_retries:
            try:
                start_time = time.time()
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
                        raise  # 拋出最後一個錯誤
                    retry_count += 1
                finally:
                    session.close()
                    logger.debug(
                        f"數據庫會話結束，耗時 {time.time() - start_time:.2f} 秒"
                    )
            except Exception as e:
                last_error = e
                retry_info = f"(嘗試 {retry_count + 1}/{max_retries})"
                error_msg = f"創建數據庫會話失敗 {retry_info}: {str(last_error)}"
                logger.error(error_msg)
                if retry_count == max_retries - 1:
                    raise
                retry_count += 1

        raise RuntimeError("無法創建數據庫會話")

    def with_transaction(
        self,
        fn: Callable[..., T],
        *args: Any,
        isolation_level: str | None = None,
        **kwargs: Any,
    ) -> T:
        """執行具有事務性質的數據庫操作，可傳遞額外參數給回調函數

        Args:
            fn: 回調函數，第一個參數必須是Session，其後可接受任意額外參數
            *args: 傳遞給回調函數的位置參數
            isolation_level: 事務隔離級別（如 "READ COMMITTED"、"SERIALIZABLE"等）
            **kwargs: 傳遞給回調函數的關鍵字參數

        Returns:
            函數執行的結果

        Raises:
            Exception: 當資料庫操作失敗時拋出相應異常
        """
        with self.with_session() as session:
            if isolation_level:
                if self._db_settings.DB == "supabase":
                    # 為Supabase/PostgreSQL設置隔離級別
                    stmt = f"SET TRANSACTION ISOLATION LEVEL {isolation_level}"
                    _ = session.execute(text(stmt))
                elif (
                    self._db_settings.DB == "sqlite"
                    and isolation_level.upper() != "SERIALIZABLE"
                ):
                    # SQLite只支持SERIALIZABLE隔離級別，記錄警告
                    logger.warning(
                        f"SQLite只支持SERIALIZABLE隔離級別，忽略指定的{isolation_level}隔離級別"
                    )

            return fn(session, *args, **kwargs)


@lru_cache(maxsize=1)
def get_core_db() -> Database:
    """獲取全局數據庫實例，使用LRU緩存確保單例模式

    Returns:
        Database: 數據庫管理器實例
    """
    return Database(db_settings=get_settings())
