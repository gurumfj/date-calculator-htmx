import logging
import sqlite3
from enum import Enum

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

logger = logging.getLogger(__name__)

router = APIRouter()
html_templates = Jinja2Templates(directory="src/server/templates")
sql_templates = Jinja2Templates(directory="src/server/templates/sql")
DB_PATH = "./data/sqlite.db"


class View(Enum):
    TABLE = "table"
    TABLE_ROWS = "table-rows"
    CARDS = "cards"
    CARD_LIST = "card-list"


# 請求參數常數
DEFAULT_CHICKEN_BREED = "古早"
DEFAULT_LIMIT_CARDS = 20
DEFAULT_LIMIT_TABLE = 50


def get_db_connection():
    """取得資料庫連線"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def get_batch_data(chicken_breed: str, limit: int = 50, offset: int = 0, batch_name: str | None = None):
    """共用的資料獲取邏輯"""
    conn = get_db_connection()
    cursor = conn.cursor()

    # 渲染SQL模板
    sql_query = sql_templates.get_template("batch_summary_v2.sql").render(limit=True, batch_name=batch_name)

    # 準備查詢參數
    params = {"chicken_breed": chicken_breed, "limit": limit, "offset": offset}

    # 如果有批次名稱搜尋，加入LIKE參數
    if batch_name:
        params["batch_name"] = f"%{batch_name}%"

    # 執行查詢
    cursor.execute(sql_query, params)

    batches = [dict(row) for row in cursor.fetchall()]
    conn.close()

    return batches


def get_chicken_breeds():
    """取得所有雞種"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT chicken_breed FROM breed ORDER BY chicken_breed")
    chicken_breeds = [row[0] for row in cursor.fetchall()]
    conn.close()
    return chicken_breeds


@router.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """批次摘要主頁面"""
    try:
        chicken_breeds = get_chicken_breeds()
        chicken_breed = request.query_params.get(
            "chicken_breed", chicken_breeds[0] if chicken_breeds else DEFAULT_CHICKEN_BREED
        )
        batch_name = request.query_params.get("batch_name", "")

        # 初始載入資料
        batches = get_batch_data(
            chicken_breed, limit=DEFAULT_LIMIT_CARDS, offset=0, batch_name=batch_name if batch_name else None
        )

        return html_templates.TemplateResponse(
            "batches/index.html",
            {
                "request": request,
                "batches": batches,
                "chicken_breeds": chicken_breeds,
                "chicken_breed": chicken_breed,
                "batch_name": batch_name,
                "has_more": len(batches) == DEFAULT_LIMIT_CARDS,
                "next_offset": DEFAULT_LIMIT_CARDS,
                "view": View.CARDS.value,
            },
        )
    except Exception as e:
        logger.error(f"批次頁面錯誤: {e}")
        return html_templates.TemplateResponse("components/error.html", {"request": request, "error": str(e)})


@router.get("/data", response_class=HTMLResponse)
async def data(request: Request):
    """批次資料端點 - 支援卡片和表格視圖"""
    try:
        chicken_breed = request.query_params.get("chicken_breed", DEFAULT_CHICKEN_BREED)
        batch_name = request.query_params.get("batch_name", "")
        view = request.query_params.get("view", "cards")
        limit = int(request.query_params.get("limit", DEFAULT_LIMIT_CARDS))
        offset = int(request.query_params.get("offset", 0))

        batches = get_batch_data(chicken_breed, limit, offset, batch_name if batch_name else None)

        match view:
            case View.TABLE_ROWS.value:
                template_name = "batches/table.html"
            case View.CARDS.value:
                template_name = "batches/cards.html"
            case View.CARD_LIST.value:
                template_name = "batches/cards.html"
            case View.TABLE.value:
                template_name = "batches/table.html"
            case _:
                raise ValueError(f"Invalid view: {view}")
        context = {
            "request": request,
            "batches": batches,
            "chicken_breed": chicken_breed,
            "batch_name": batch_name,
            "has_more": len(batches) == limit,
            "next_offset": offset + limit,
            "view": view,
        }

        return html_templates.TemplateResponse(template_name, context)
    except Exception as e:
        logger.error(f"批次資料錯誤: {e}")
        return html_templates.TemplateResponse("components/error.html", {"request": request, "error": str(e)})
