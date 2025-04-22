import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

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

# --- Constants for event keys ---
STARTED = "started"
COMPLETED = "completed"
FAILED = "failed"


@dataclass
class ProcessContent:
    """Holds the parameters and results for a processing task."""

    source_params: dict[str, Any]
    response: IResponse | None = field(
        default=None, metadata={"description": "處理結果"}
    )


@dataclass
class ProcessorEventPayload:
    """Payload for processor-related events."""

    event: Enum
    content: ProcessContent


# --- Configuration for different processors ---
@dataclass
class ProcessorConfig:
    """Configuration for a single processor type."""

    name: str
    processor_class: type[IProcessor[Any, Any]]
    events: dict[str, Enum]


PROCESSOR_CONFIGS: list[ProcessorConfig] = [
    ProcessorConfig(
        name="sales",
        processor_class=SaleRecordProcessor,
        events={
            STARTED: ProcessedEvent.SALES_PROCESSING_STARTED,
            COMPLETED: ProcessedEvent.SALES_PROCESSING_COMPLETED,
            FAILED: ProcessedEvent.SALES_PROCESSING_FAILED,
        },
    ),
    ProcessorConfig(
        name="breeds",
        processor_class=BreedRecordProcessor,
        events={
            STARTED: ProcessedEvent.BREEDS_PROCESSING_STARTED,
            COMPLETED: ProcessedEvent.BREEDS_PROCESSING_COMPLETED,
            FAILED: ProcessedEvent.BREEDS_PROCESSING_FAILED,
        },
    ),
    ProcessorConfig(
        name="feeds",
        processor_class=FeedRecordProcessor,
        events={
            STARTED: ProcessedEvent.FEEDS_PROCESSING_STARTED,
            COMPLETED: ProcessedEvent.FEEDS_PROCESSING_COMPLETED,
            FAILED: ProcessedEvent.FEEDS_PROCESSING_FAILED,
        },
    ),
]


class ProcessExecutor:
    """
    處理器執行器
    Listens for 'started' events, executes the corresponding processor,
    and publishes 'completed' or 'failed' events along with broadcast messages.
    """

    _event_bus: EventBus
    _processors: dict[str, IProcessor[Any, Any]]
    _event_map: dict[str, dict[str, Enum]]
    # Map 'started' event enum directly to processor name (key) for faster lookup
    _start_event_to_processor_key: dict[Enum, str]

    def __init__(self, event_bus: EventBus) -> None:
        """
        Initializes the ProcessExecutor.

        Args:
            event_bus: The event bus instance for publishing and subscribing.
        """
        self._event_bus = event_bus
        self._processors = {}
        self._event_map = {}
        self._start_event_to_processor_key = {}

        # Initialize processors and event maps based on configuration
        for config in PROCESSOR_CONFIGS:
            processor_name = config.name
            # Instantiate the processor
            self._processors[processor_name] = config.processor_class()
            self._event_map[processor_name] = config.events
            start_event = config.events[STARTED]
            self._start_event_to_processor_key[start_event] = processor_name

            # Register event handlers for this processor type
            self._event_bus.register(start_event, self.handle_start)
            self._event_bus.register(config.events[COMPLETED], self._handle_response)
            self._event_bus.register(config.events[FAILED], self._handle_response)

        logger.info(
            f"ProcessExecutor initialized with processors: {list(self._processors.keys())}"
        )

    def handle_start(self, payload: ProcessorEventPayload) -> None:
        """
        Handles the 'started' event for a specific processor.
        Executes the processor and publishes the outcome.

        Args:
            payload: The event payload containing the event type and source parameters.
        """
        # Avoid circular import
        from cleansales_backend.core import get_core_db

        start_event = payload.event
        logger.debug(f"Handling start event: {start_event.name}")

        processor_key = self._start_event_to_processor_key.get(start_event)
        if not processor_key:
            logger.error(f"No processor configured for start event: {start_event.name}")
            return

        processor = self._processors[processor_key]
        workflow_events = self._event_map[processor_key]

        try:
            # Execute the processor logic within a database transaction
            response = get_core_db().with_transaction(
                processor.execute, **payload.content.source_params
            )
            logger.debug(
                f"Processor {processor_key} executed. Success: {response.success}"
            )

            # --- Decide outcome event ---
            if response.content.validation.data_existed:
                logger.warning(
                    f"Data already existed for {processor_key}. Skipping further processing and event publishing."
                )
                # Optionally, publish a specific 'skipped' or 'duplicate' event if needed
                return  # Stop processing if data already exists

            if response.success:
                outcome_event_type = COMPLETED
                log_level = logging.INFO
                status_message = "completed successfully"
            else:
                outcome_event_type = FAILED
                log_level = logging.ERROR
                status_message = "failed"

            outcome_event = workflow_events[outcome_event_type]
            logger.log(
                log_level,
                f"Processing for {processor_key} {status_message}. Publishing {outcome_event.name}.",
            )

            # Publish the completed/failed event
            self._event_bus.publish(
                ProcessorEventPayload(
                    event=outcome_event,
                    content=ProcessContent(
                        source_params=payload.content.source_params,
                        response=response,
                    ),
                )
            )

        except Exception as e:
            # Handle unexpected errors during processing or transaction
            logger.exception(
                f"Unexpected error during processing for {processor_key} with event {start_event.name}: {e}"
            )
            # Publish a failed event with minimal info if possible
            fail_event = workflow_events[FAILED]
            try:
                self._event_bus.publish(
                    ProcessorEventPayload(
                        event=fail_event,
                        content=ProcessContent(
                            source_params=payload.content.source_params,
                            # No meaningful response available in case of exception
                            response=None,
                        ),
                    )
                )
            except Exception as pub_e:
                logger.error(
                    f"Failed to publish failure event {fail_event.name} after exception: {pub_e}"
                )

    def _format_broadcast_message(self, response: IResponse) -> list[LineObject] | None:
        """Formats the broadcast message based on the processor response."""
        # Basic message structure
        msg = [LineObject(Head.TITLE, text=f"{response.content.processor_name}:")]

        # Validation summary
        validated_count = len(response.content.validation.validated_records)
        error_count = len(response.content.validation.error_records)
        if validated_count > 0 or error_count > 0:
            msg.append(
                LineObject(
                    Head.TEXT,
                    text=f"驗證資料 {validated_count} 筆，{error_count} 筆略過",
                )
            )

        # Infrastructure changes summary (if available)
        if not response.content.infrastructure:
            return msg  # Return basic message if no infra details

        infra = response.content.infrastructure
        if len(infra.new_names) > 0:
            msg.append(LineObject(Head.TEXT, text=f"新增 {len(infra.new_names)} 筆:"))
            msg.extend([LineObject(Head.BULLET, text=name) for name in infra.new_names])
        if len(infra.delete_names) > 0:
            msg.append(
                LineObject(Head.TEXT, text=f"刪除 {len(infra.delete_names)} 筆:")
            )
            msg.extend(
                [LineObject(Head.BULLET, text=name) for name in infra.delete_names]
            )

        return msg

    def _handle_response(self, payload: ProcessorEventPayload) -> None:
        """
        Handles 'completed' or 'failed' events.
        Formats and publishes a broadcast message based on the response.
        """
        response = payload.content.response
        event_type = payload.event.name  # For logging

        if not response:
            logger.error(
                f"Received event {event_type} but no response content found in payload."
            )
            # Optionally publish a generic error broadcast message
            return

        # Log based on the event type (completed/failed)
        if COMPLETED in event_type:
            logger.info(
                f"Handling completion event: {event_type} for {response.content.processor_name}"
            )
        elif FAILED in event_type:
            logger.error(
                f"Handling failure event: {event_type} for {response.content.processor_name}"
            )
        else:
            logger.warning(f"Handling unexpected response event: {event_type}")

        # Format the broadcast message
        broadcast_msg_content = self._format_broadcast_message(response)

        if broadcast_msg_content:
            logger.debug(f"Publishing broadcast message for event: {event_type}")
            try:
                self._event_bus.publish(
                    BroadcastEventPayload(
                        event=BroadcastEvent.SEND_MESSAGE,
                        content=broadcast_msg_content,
                    )
                )
            except Exception as e:
                logger.exception(
                    f"Failed to publish broadcast message for event {event_type}: {e}"
                )
        else:
            logger.debug(f"No broadcast message generated for event: {event_type}")
