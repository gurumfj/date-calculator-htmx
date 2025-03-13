"""TODO: query location sales data from the database"""

import json
from dataclasses import asdict
from datetime import datetime

from mcp.server import FastMCP

from cleansales_refactor import Database, settings
from cleansales_refactor.repositories import BreedRepository, SaleRepository
from cleansales_refactor.services import QueryService

mcp = FastMCP("cleansales-server")

db = Database(settings.DB_PATH)
sale_repository = SaleRepository()
breed_repository = BreedRepository()
query_service = QueryService(breed_repository, sale_repository)


@mcp.tool(name="today", description="Get the current date in YYYY-MM-DD format")
def get_today() -> str:
    return datetime.now().strftime("%Y-%m-%d")


@mcp.resource(
    uri="sales://recently_sold",
    name="recently sold",
    description="Get recently sold products",
    mime_type="application/json",
)
def get_recently_sold() -> str:
    with db.get_session() as session:
        sales = query_service.get_sales_data(session, limit=30, offset=0)
        return json.dumps(
            [asdict(sale) for sale in sales], default=str, ensure_ascii=False
        )


if __name__ == "__main__":
    mcp.run()
