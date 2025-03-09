from .cli import main
from .core import Database, event_bus, settings
from .domain.models import BreedRecord, SaleRecord
from .services import CleanSalesService


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
    "Database",
    "event_bus",
    "settings",
    # domain models
    "BreedRecord",
    "SaleRecord",
    # services
    "CleanSalesService",
    # entry point
    "main",
    "run_api",
]
