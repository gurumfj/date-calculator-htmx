from enum import Enum


class ProcessEvent(Enum):
    SALES_PROCESSING_STARTED = "sales_processing_started"
    SALES_PROCESSING_COMPLETED = "sales_processing_completed"
    SALES_PROCESSING_FAILED = "sales_processing_failed"

    BREEDS_PROCESSING_STARTED = "breeds_processing_started"
    BREEDS_PROCESSING_COMPLETED = "breeds_processing_completed"
    BREEDS_PROCESSING_FAILED = "breeds_processing_failed"
