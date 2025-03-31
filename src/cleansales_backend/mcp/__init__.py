from . import batch_tools, server


def main() -> None:
    server.mcp.run()


__all__ = ["main", "server", "batch_tools"]
