from dataclasses import dataclass
from enum import Enum


class ProcessedEvent(str, Enum):
    """處理事件枚舉"""

    SALES_PROCESSING_STARTED = "販售資料上傳開始"
    SALES_PROCESSING_COMPLETED = "販售資料上傳完成"
    SALES_PROCESSING_FAILED = "販售資料上傳失敗"
    BREEDS_PROCESSING_STARTED = "入雛資料上傳開始"
    BREEDS_PROCESSING_COMPLETED = "入雛資料上傳完成"
    BREEDS_PROCESSING_FAILED = "入雛資料上傳失敗"
    FEEDS_PROCESSING_STARTED = "飼料記錄上傳開始"
    FEEDS_PROCESSING_COMPLETED = "飼料記錄上傳完成"
    FEEDS_PROCESSING_FAILED = "飼料記錄上傳失敗"


class BroadcastEvent(Enum):
    SEND_MESSAGE = "Send Message"
    SEND_DOCUMENT = "Send Document"


class Head(Enum):
    TITLE = "title"
    TEXT = "text"
    BULLET = "bullet"


@dataclass
class LineObject:
    head: Head
    text: str


@dataclass
class BroadcastEventPayload:
    event: Enum
    content: list[LineObject]


__all__ = [
    "ProcessedEvent",
    "BroadcastEvent",
]
