# from .cli import main
from .core import Database, event_bus, settings

# def run_mcp_server() -> None:
#     import asyncio

#     from cleansales_refactor.mcp import mcp_server

#     asyncio.run(mcp_server.main())


# if __name__ == "__main__":
#     main()

__all__ = [
    # core
    "Database",
    "event_bus",
    "settings",
    # entry point
    # "main",
    # "run_api",
    # "run_mcp_server",
]
