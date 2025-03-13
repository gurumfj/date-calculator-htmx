from datetime import datetime
from enum import Enum
from typing import Generic, TypeVar

from sqlmodel import Field, SQLModel


class ProcessingEvent(Enum):
    """事件類型"""

    ADDED = "added"
    DELETED = "deleted"
    UPDATED = "updated"
    NEW_MD5 = "new_md5"


class ORMModel(SQLModel):
    """基礎 ORM 模型"""

    unique_id: str = Field(primary_key=True, unique=True, index=True)
    event: str = Field(default="")
    updated_at: datetime = Field(default_factory=datetime.now)
    event_source_id: int | None


M = TypeVar("M", bound=ORMModel)


class BaseEventSource(SQLModel, Generic[M]):
    """基礎事件來源資料表模型"""

    # __abstract__ = True

    id: int = Field(default=0, primary_key=True, index=True)
    source_name: str
    source_md5: str
    event: str
    count: int
    created_at: datetime = Field(default_factory=datetime.now)

    # 移除直接的 list 類型定義，改由子類別定義具體的關係
    # records: list[M]


class ErrorRecord(SQLModel, table=True):
    """基礎錯誤記錄資料表模型"""

    id: int | None = Field(default=None, primary_key=True)
    message: str
    data: str
    extra: str
    timestamp: str
