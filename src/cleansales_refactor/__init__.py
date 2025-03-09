from .__main__ import main
from .core.event_bus import event_bus
from .domain.models import BatchAggregate, BatchState, BreedRecord, SaleRecord
from .exporters import (
    BaseSQLiteExporter,
    BreedSQLiteExporter,
    Database,
    IExporter,
    ProcessingEvent,
    SaleSQLiteExporter,
)
from .processors import BreedsProcessor, IProcessor, SalesProcessor
from .services.cleansales_service import CleanSalesService
from .services.data_service import DataService
from .shared.models import ErrorMessage, ProcessingResult, Response, SourceData


def run_api() -> None:
    import uvicorn

    uvicorn.run(
        "cleansales_refactor.api.app:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        reload_dirs=["src/cleansales_refactor"],
    )


# if __name__ == "__main__":
#     main()

__all__ = [
    "CleanSalesService",
    "DataService",
    "ErrorMessage",
    "ProcessingResult",
    "Response",
    "SourceData",
    "BreedRecord",
    "SaleRecord",
    "BatchAggregate",
    "BatchState",
    "BreedsProcessor",
    "SalesProcessor",
    "IProcessor",
    "BaseSQLiteExporter",
    "BreedSQLiteExporter",
    "SaleSQLiteExporter",
    "Database",
    "IExporter",
    "ProcessingEvent",
    "main",
    "run_api",
    "event_bus",
]
