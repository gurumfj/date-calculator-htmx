"""Sales route definitions."""

import logging
from datetime import datetime
from sqlite3 import Connection, Row
from typing import Any, Dict

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter()
templates = Jinja2Templates(directory="src/server/templates")
sql_templates = Jinja2Templates(directory="src/server/templates/sql")


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
async def query_sales(request: Request, page: int = 1, search: str | None = None, page_size: int = 100):
    """查詢銷售資料"""
    # 參數驗證防止DoS攻擊
    page_size = min(max(page_size, 1), 1000)  # 限制1-1000
    offset = max((page - 1) * page_size, 0)  # 不允許負數

    try:
        query_template = sql_templates.get_template("sales_query.sql")
        query = query_template.render(search=search and search.strip())

        params: Dict[str, Any] = {"limit": page_size, "offset": offset}
        if search and search.strip():
            params["search"] = f"%{search}%"

        result = connection.execute(query, params).fetchall()

        data = [SaleRecord.model_validate(dict(row)) for row in result]

        context = {"request": request, "sales": data, "page": page, "search": search or ""}

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
