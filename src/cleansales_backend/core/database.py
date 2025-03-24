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
    _db_path: Path

    def __init__(self, db_path: Path | str) -> None:
        self._db_path = Path(db_path) if isinstance(db_path, str) else db_path
        self._db_path.parent.mkdir(exist_ok=True)

        # 創建引擎時啟用連接池，並添加 SQLite 優化設置
        connect_args = {
            "timeout": 30,  # 連接超時時間
            "check_same_thread": False,  # 允許跨線程訪問
        }

        self._engine = create_engine(
            f"sqlite:///{self._db_path}",
            echo=settings.DB_ECHO,
            pool_size=5,  # 減小連接池大小以避免資源爭用
            max_overflow=10,
            pool_timeout=30,
            pool_recycle=300,  # 更頻繁地回收連接
            pool_pre_ping=True,  # 在使用前測試連接
            connect_args=connect_args,
        )

        # 啟用外鍵約束
        with self._engine.connect() as conn:
            _ = conn.execute(text("PRAGMA foreign_keys=ON"))
            conn.commit()

        # 創建表
        SQLModel.metadata.create_all(self._engine)

        # 應用數據庫優化
        # setup_db_optimizations(self._engine)

        # 啟動數據庫監控
        monitor.start_monitoring(self._engine)

        logger.info(f"Database created at {self._db_path.absolute()}")

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
                logger.debug(f"Database path: {self._db_path}")
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
