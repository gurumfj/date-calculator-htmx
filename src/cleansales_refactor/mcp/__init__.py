from . import server


def main():
    server.mcp.run()


__all__ = ["main", "server"]
