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

from cleansales_backend.processors import BreedRecordORM, SaleRecordORM
from cleansales_backend.processors.interface.processors_interface import IORMModel

from .config import settings
from .db_monitor import monitor

# 註冊所有的 ORM 模型
_orm_models: list[type[IORMModel]] = [BreedRecordORM, SaleRecordORM]

logger = logging.getLogger(__name__)


class Database:
    _engine: Engine
    _db_path: Path

    def __init__(self, db_path: Path | str) -> None:
        self._db_path = Path(db_path) if isinstance(db_path, str) else db_path
        self._db_path.parent.mkdir(exist_ok=True)

        # 創建引擎時啟用連接池
        self._engine = create_engine(
            f"sqlite:///{self._db_path}",
            echo=settings.DB_ECHO,
            pool_size=10,
            max_overflow=20,
            pool_timeout=30,
            pool_recycle=1800
        )
        
        # 創建表
        SQLModel.metadata.create_all(self._engine)
        
        # 應用數據庫優化
        from .db_optimizations import setup_db_optimizations
        setup_db_optimizations(self._engine)
        
        # 啟動數據庫監控
        monitor.start_monitoring(self._engine)
        
        logger.info(f"Database created at {self._db_path.absolute()}")

    def get_session(self) -> Generator[Session, None, None]:
        """獲取數據庫會話

        使用 context manager 模式管理 session 生命週期，確保資源正確釋放
        自動處理交易的提交和回滾

        Yields:
            Session: 數據庫會話實例，可用於執行查詢和修改操作

        Raises:
            Exception: 當資料庫操作失敗時拋出相應異常
        """
        # hint db path
        logger.debug(f"Database path: {self._db_path}")
        # 使用 with 語句自動管理 session 生命週期
        with Session(self._engine) as session:
            try:
                logger.debug("開始數據庫會話")
                yield session
                # 如果沒有異常發生，自動提交更改
                # session.commit()
                # logger.debug("數據庫會話提交成功")
            except Exception as e:
                # 發生異常時回滾更改
                session.rollback()
                logger.error(f"數據庫操作失敗: {str(e)}")
                raise
            finally:
                logger.debug("數據庫會話結束")

    @contextmanager
    def with_session(self) -> Generator[Session, None, None]:
        """
        提供上下文管理器，確保 session 的生命週期管理
        """
        yield from self.get_session()
