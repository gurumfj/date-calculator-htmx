from event_bus import EventBus, TelegramNotifier

from .events import ProcessEvent

# 初始化事件匯流排
event_bus = EventBus()

# 初始化 Telegram 通知器
telegram_notifier = TelegramNotifier(
    event_bus,
    [
        ProcessEvent.SALES_PROCESSING_STARTED,
        ProcessEvent.SALES_PROCESSING_COMPLETED,
        ProcessEvent.SALES_PROCESSING_FAILED,
        ProcessEvent.BREEDS_PROCESSING_STARTED,
        ProcessEvent.BREEDS_PROCESSING_COMPLETED,
        ProcessEvent.BREEDS_PROCESSING_FAILED,
    ],
)


def get_event_bus() -> EventBus:
    """獲取事件匯流排的依賴注入函數"""
    return event_bus
