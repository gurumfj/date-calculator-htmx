from .__main__ import main
from .core.event_bus import event_bus
from .domain.models import BreedRecord, SaleRecord
from .exporters.database import Database
from .services.cleansales_service import CleanSalesService
from .services.cli_service import CLIService


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
    # core
    "event_bus",
    "Database",
    # domain models
    "BreedRecord",
    "SaleRecord",
    # services
    "CleanSalesService",
    "CLIService",
    # entry point
    "main",
    "run_api",
]
