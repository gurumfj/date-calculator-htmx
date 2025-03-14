from . import server


def main() -> None:
    server.mcp.run()


__all__ = ["main", "server"]
