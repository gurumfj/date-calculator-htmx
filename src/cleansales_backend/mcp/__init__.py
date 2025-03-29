from . import server, batch_tools


def main() -> None:
    server.mcp.run()


__all__ = ["main", "server", "batch_tools"]
