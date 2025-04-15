import logging
from dataclasses import dataclass
from enum import Enum
from typing import Any

from pydantic import Field

from cleansales_backend.event_bus import EventBus
from cleansales_backend.event_bus.events import (
    BroadcastEvent,
    BroadcastEventPayload,
    Head,
    LineObject,
    ProcessedEvent,
)
from cleansales_backend.processors import (
    BreedRecordProcessor,
    FeedRecordProcessor,
    SaleRecordProcessor,
)
from cleansales_backend.processors.interface.processors_interface import (
    IProcessor,
    IResponse,
)

logger = logging.getLogger(__name__)


@dataclass
class ProcessContent:
    source_params: dict[str, Any]
    response: IResponse | None = Field(default=None, description="處理結果")


@dataclass
class ProcessorEventPayload:
    event: Enum
    content: ProcessContent


class ProcessExecutor:
    """處理器執行器"""

    _event_bus: EventBus
    _process_event_dict: dict[str, dict[str, Enum]]
    _process_dict: dict[str, IProcessor[Any, Any]]

    def __init__(self, event_bus: EventBus) -> None:
        self._event_bus = event_bus
        self._process_dict = {
            "sales": SaleRecordProcessor(),
            "breeds": BreedRecordProcessor(),
            "feeds": FeedRecordProcessor(),
        }
        self._process_event_dict = {
            "sales": {
                "started": ProcessedEvent.SALES_PROCESSING_STARTED,
                "completed": ProcessedEvent.SALES_PROCESSING_COMPLETED,
                "failed": ProcessedEvent.SALES_PROCESSING_FAILED,
            },
            "breeds": {
                "started": ProcessedEvent.BREEDS_PROCESSING_STARTED,
                "completed": ProcessedEvent.BREEDS_PROCESSING_COMPLETED,
                "failed": ProcessedEvent.BREEDS_PROCESSING_FAILED,
            },
            "feeds": {
                "started": ProcessedEvent.FEEDS_PROCESSING_STARTED,
                "completed": ProcessedEvent.FEEDS_PROCESSING_COMPLETED,
                "failed": ProcessedEvent.FEEDS_PROCESSING_FAILED,
            },
        }

        # register start events
        for workflow in self._process_event_dict.values():
            self._event_bus.register(workflow["started"], self.handle_start)
            self._event_bus.register(workflow["completed"], self._handle_response)
            self._event_bus.register(workflow["failed"], self._handle_response)

    def handle_start(self, payload: ProcessorEventPayload) -> None:
        """處理器開始

        Args:
            payload (ProcessorEventPayload): 要執行的事件
        """
        # 延遲導入 core_db 以避免循環導入
        from cleansales_backend.core import get_core_db

        logger.debug(f"開始處理事件: {payload.event}")
        for k, workflow in self._process_event_dict.items():
            if payload.event != workflow["started"]:
                continue

            response = get_core_db().with_transaction(
                self._process_dict[k].execute, **payload.content.source_params
            )

            # ---- publish event ----
            if not response.success:
                logger.error("處理失敗")
                self._event_bus.publish(
                    ProcessorEventPayload(
                        event=workflow["failed"],
                        content=ProcessContent(
                            source_params=payload.content.source_params,
                            response=response,
                        ),
                    )
                )
                return

            if response.success and response.content.validation.data_existed:
                logger.info("資料已存在，跳過處理")
                return

            self._event_bus.publish(
                ProcessorEventPayload(
                    event=workflow["completed"],
                    content=ProcessContent(
                        source_params=payload.content.source_params,
                        response=response,
                    ),
                )
            )
            return

    def _handle_response(self, payload: ProcessorEventPayload) -> None:
        if not payload.content.response:
            logger.error("處理失敗")
            return

        response = payload.content.response

        msg = [LineObject(Head.TITLE, text=f"{response.content.processor_name}:")]
        if (
            len(response.content.validation.validated_records) > 0
            and len(response.content.validation.error_records) > 0
        ):
            msg.append(
                LineObject(
                    Head.TEXT,
                    text=f"驗證資料{len(response.content.validation.validated_records)}筆，{len(response.content.validation.error_records)}筆略過",
                )
            )

        if not response.content.infrastructure:
            return

        if len(response.content.infrastructure.new_names) > 0:
            msg.append(
                LineObject(
                    Head.TEXT,
                    text=f"新增{len(response.content.infrastructure.new_names)}筆",
                )
            )
            msg.extend(
                [
                    LineObject(Head.BULLET, text=f"{name}")
                    for name in response.content.infrastructure.new_names
                ]
            )
        if len(response.content.infrastructure.delete_names) > 0:
            msg.append(
                LineObject(
                    Head.TEXT,
                    text=f"刪除{len(response.content.infrastructure.delete_names)}筆",
                )
            )
            msg.extend(
                [
                    LineObject(Head.BULLET, text=f"{name}")
                    for name in response.content.infrastructure.delete_names
                ]
            )

        self._event_bus.publish(
            BroadcastEventPayload(
                event=BroadcastEvent.SEND_MESSAGE,
                content=msg,
            )
        )

    def execute_update_batch_aggregate(self) -> None:
        """執行批次統計更新腳本

        這個方法會執行批次統計更新的腳本，會將所有批次記錄的統計資料更新到最新。
        這個方法主要是給 CLI 使用的。
        """
        from cleansales_backend.core import get_core_db
        from cleansales_backend.processors import (
            BreedRecordProcessor,
            FeedRecordProcessor,
            SaleRecordProcessor,
        )

        _db = get_core_db()
        processores: list[IProcessor[Any, Any]] = [
            BreedRecordProcessor(),
            FeedRecordProcessor(),
            SaleRecordProcessor(),
        ]

        with _db.with_session() as session:
            for processor in processores:
                print("開始更新批次統計", processor.set_processor_name())
                orms = processor.get_all_orm(session)
                for orm in orms:
                    _ = processor.update_batch_aggregate(session, orm)


if __name__ == "__main__":
    process_executor = ProcessExecutor(EventBus())
    process_executor.execute_update_batch_aggregate()
