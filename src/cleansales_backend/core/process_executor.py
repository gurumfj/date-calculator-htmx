import logging
from enum import Enum

from cleansales_backend.core.event_bus import Event, EventBus
from cleansales_backend.core.events import ProcessEvent, SystemEvent
from cleansales_backend.core.telegram_notifier import LineObject
from cleansales_backend.processors import (
    BreedRecordProcessor,
    FeedRecordProcessor,
    SaleRecordProcessor,
)
from cleansales_backend.processors.interface.processors_interface import IResponse

logger = logging.getLogger(__name__)


class ProcessExecutor:
    """處理器執行器"""

    _event_bus: EventBus
    _sales_processor: SaleRecordProcessor
    _breeds_processor: BreedRecordProcessor
    _feeds_processor: FeedRecordProcessor

    def __init__(self, event_bus: EventBus, register_events: list[Enum]) -> None:
        self._event_bus = event_bus
        self._sales_processor = SaleRecordProcessor()
        self._breeds_processor = BreedRecordProcessor()
        self._feeds_processor = FeedRecordProcessor()

        for event in register_events:
            self._event_bus.register(event, self.execute)

    def execute(self, event: Event) -> None:
        """執行處理器

        Args:
            event (Event): 要執行的事件
        """
        # 延遲導入 core_db 以避免循環導入
        from cleansales_backend.core import core_db

        logger.debug(f"開始處理事件: {event.event}")
        with core_db.with_session() as session:
            process_response: IResponse = (
                self._sales_processor.execute(session=session, **event.content)
                if event.event == ProcessEvent.SALES_PROCESSING_STARTED
                else self._breeds_processor.execute(session=session, **event.content)
                if event.event == ProcessEvent.BREEDS_PROCESSING_STARTED
                else self._feeds_processor.execute(session=session, **event.content)
                if event.event == ProcessEvent.FEEDS_PROCESSING_STARTED
                else IResponse(success=False, message="Invalid event type")
            )
        if not process_response.success:
            logger.error("處理失敗")
            return

        if not process_response.content:
            logger.info("沒有處理結果")
            return

        pr = process_response.content
        logger.debug(f"處理完成: {pr}")
        if not pr.new_keys and not pr.delete_keys:
            logger.info("沒有新記錄需要添加，沒有記錄需要刪除")
            return
        self._event_bus.publish(
            Event(
                event=ProcessEvent.SALES_PROCESSING_COMPLETED
                if event.event == ProcessEvent.SALES_PROCESSING_STARTED
                else ProcessEvent.BREEDS_PROCESSING_COMPLETED
                if event.event == ProcessEvent.BREEDS_PROCESSING_STARTED
                else ProcessEvent.FEEDS_PROCESSING_COMPLETED,
                message="處理完成",
                content={
                    "telegram_message": [
                        LineObject(
                            format="title",
                            text=f"{pr.processor_name}: ",
                        ),
                        LineObject(
                            format="title",
                            text=f"{len(pr.new_keys)} records to be added",
                        ),
                        *[
                            LineObject(
                                format="bullet",
                                text=f"{location}",
                            )
                            for location in pr.new_names
                        ],
                        LineObject(
                            format="title",
                            text=f"{len(pr.delete_keys)} records to be deleted",
                        ),
                        *[
                            LineObject(
                                format="bullet",
                                text=f"{location}",
                            )
                            for location in pr.delete_names
                        ],
                    ]
                },
            )
        )
        self._event_bus.publish(
            Event(
                event=SystemEvent.CACHE_CLEAR,
                message=f"{event.event} 完成，開始清除緩存",
                content={},
            )
        )
