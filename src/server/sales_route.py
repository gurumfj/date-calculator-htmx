import logging
from datetime import datetime
from sqlite3 import Connection, Row

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter()
templates = Jinja2Templates(directory="src/server/templates")


# def create_data_service() -> DataServiceInterface:
#     return SQLiteDataService(db_path="./data/sqlite.db")


# cached_data = create_data_service()

connection = Connection("./data/sqlite.db")
connection.row_factory = Row


class SaleRecord(BaseModel):
    sale_date: datetime
    batch_name: str
    customer: str
    male_count: int
    female_count: int
    avg_price: float | None
    male_avg_weight: float | None
    female_avg_weight: float | None
    male_price: float | None
    female_price: float | None


@router.get("/q", response_class=HTMLResponse)
async def query_sales(request: Request, offset: int = 0, search: str | None = None, page_size: int = 100):
    """查詢銷售資料"""
    base_query = """
        SELECT
            sale_date,
            batch_name,
            customer,
            male_count,
            female_count,
            CASE 
                WHEN total_price IS NULL OR (male_count + female_count) = 0 THEN NULL
                ELSE total_price / (male_count + female_count)
            END as avg_price,
            CASE 
                WHEN male_count = 0 OR total_weight IS NULL THEN NULL
                ELSE ((total_weight - male_count * 0.8) / (male_count + female_count)) + 0.8
            END as male_avg_weight,
            CASE 
                WHEN female_count = 0 OR total_weight IS NULL THEN NULL
                ELSE (total_weight - male_count * 0.8) / (male_count + female_count)
            END as female_avg_weight,
            male_price,
            female_price
        FROM sale
    """
    filter_query = " WHERE batch_name LIKE :search OR customer LIKE :search"
    sort_query = " ORDER BY sale_date DESC"
    offset_query = " LIMIT :page_size OFFSET :offset"
    try:
        if search and search.strip() != "":
            result = connection.execute(
                base_query + filter_query + sort_query + offset_query,
                {"search": f"%{search}%", "page_size": page_size, "offset": offset},
            ).fetchall()
        else:
            result = connection.execute(
                base_query + sort_query + offset_query, {"page_size": page_size, "offset": offset}
            ).fetchall()

        data = [SaleRecord.model_validate(dict(row)) for row in result]

        context = {"request": request, "sales": data, "offset": offset, "search": search or ""}

        return templates.TemplateResponse("sales/sales_rows.html", context)

    except Exception as e:
        logger.error(f"查詢銷售資料錯誤: {e}")
        return HTMLResponse(
            content='<span id="search_error" class="text-red-500" hx-swap-oob="true">錯誤輸入</span>',
            headers={"HX-Reswap": "none", "HX-Current-url": "/sales"},
        )


@router.get("/", response_class=HTMLResponse)
async def sales_index(request: Request, offset: int = 0, search: str | None = None):
    """銷售記錄主頁面"""
    try:
        context = {"request": request, "offset": offset, "search": search or ""}

        return templates.TemplateResponse("sales/index.html", context)

    except Exception as e:
        logger.error(f"銷售頁面錯誤: {e}")
        return templates.TemplateResponse("components/error.html", {"request": request, "error": str(e)})
