import json
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

# 添加千分位分隔符過濾器
def format_number(value):
    """格式化數字，添加千分位分隔符"""
    if value is None:
        return "0"
    return f"{int(value):,}"

html_templates.env.filters["format_number"] = format_number
DB_PATH = "./data/sqlite.db"


class View(Enum):
    TABLE = "table"
    TABLE_ROWS = "table-rows"
    CARDS = "cards"
    CARD_LIST = "card-list"
    PLAIN = "plain"
    PLAIN_CONTENT = "plain-content"


# 請求參數常數
DEFAULT_CHICKEN_BREED = "古早"
DEFAULT_LIMIT_CARDS = 20
DEFAULT_LIMIT_TABLE = 50
DEFAULT_LIMIT_PLAIN = 100


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
    sql_query = sql_templates.get_template("batch_summary.sql").render(batch_name=batch_name)

    # 準備查詢參數
    params = {"chicken_breed": chicken_breed, "limit": limit, "offset": offset}

    # 如果有批次名稱搜尋，加入LIKE參數
    if batch_name:
        params["batch_name"] = f"%{batch_name}%"

    # 執行查詢
    cursor.execute(sql_query, params)

    batches = []
    for row in cursor.fetchall():
        batch = dict(row)
        # 解析breed_details JSON
        if batch.get("breed_details"):
            try:
                batch["breed_details"] = json.loads(batch["breed_details"])
            except (json.JSONDecodeError, TypeError):
                batch["breed_details"] = []
        batches.append(batch)

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


def get_sales_data(batch_name: str, sale_date: str | None = None):
    """獲取特定批次的銷售數據"""
    conn = get_db_connection()
    cursor = conn.cursor()

    # 渲染SQL模板
    sql_query = sql_templates.get_template("sales.sql").render(sale_date=sale_date)

    # 準備查詢參數 - 總是包含所有必需的參數
    params = {
        "batch_name": batch_name,
        "sale_date": sale_date,  # 即使是 None 也要提供
    }

    # 執行查詢
    cursor.execute(sql_query, params)

    sales_data = []
    for row in cursor.fetchall():
        sale_record = dict(row)
        # 解析 JSON 字段
        if sale_record.get("dayage_details"):
            try:
                sale_record["dayage_details"] = json.loads(sale_record["dayage_details"])
            except (json.JSONDecodeError, TypeError):
                sale_record["dayage_details"] = []

        if sale_record.get("sales_details"):
            try:
                sale_record["sales_details"] = json.loads(sale_record["sales_details"])
            except (json.JSONDecodeError, TypeError):
                sale_record["sales_details"] = []

        sales_data.append(sale_record)

    conn.close()
    return sales_data


def get_feed_data(batch_name: str | None = None, sub_location: str | None = None):
    """獲取飼料數據"""
    conn = get_db_connection()
    cursor = conn.cursor()

    # 渲染SQL模板
    sql_query = sql_templates.get_template("feed.sql").render(batch_name=batch_name, sub_location=sub_location)

    # 準備查詢參數
    params = {}
    if batch_name:
        params["batch_name"] = batch_name
    if sub_location:
        params["sub_location"] = sub_location

    # 執行查詢
    cursor.execute(sql_query, params)

    feed_data = []
    for row in cursor.fetchall():
        feed_record = dict(row)
        # 解析 JSON 字段
        if feed_record.get("feed_details"):
            try:
                feed_details = json.loads(feed_record["feed_details"])
                # 處理每個飼料記錄的日期格式
                for feed_item in feed_details:
                    if feed_item.get("feed_date"):
                        # 如果日期格式需要調整，可以在這裡處理
                        # 例如：從 YYYY-MM-DD 轉換為其他格式
                        feed_item["feed_date"] = feed_item["feed_date"].split("T")[0]
                feed_record["feed_details"] = feed_details
            except (json.JSONDecodeError, TypeError):
                feed_record["feed_details"] = []

        feed_data.append(feed_record)

    conn.close()
    return feed_data


def get_farm_production_data(batch_name: str | None = None):
    """獲取農場生產結場數據"""
    conn = get_db_connection()
    cursor = conn.cursor()

    # 渲染SQL模板
    sql_query = sql_templates.get_template("farm_production.sql").render(batch_name=batch_name)

    # 準備查詢參數
    params = {}
    if batch_name:
        params["batch_name"] = batch_name

    # 執行查詢
    cursor.execute(sql_query, params)

    production_data = []
    for row in cursor.fetchall():
        production_record = dict(row)
        
        # 處理日期格式
        if production_record.get("created_at"):
            production_record["created_at"] = production_record["created_at"].split("T")[0]
        
        production_data.append(production_record)

    conn.close()
    return production_data


@router.get("/", response_class=HTMLResponse)
async def plain(request: Request):
    """批次摘要主頁面"""
    try:
        view = request.query_params.get("view", View.PLAIN.value)
        batch_name = request.query_params.get("batch_name", "")

        chicken_breeds = get_chicken_breeds()
        chicken_breed = request.query_params.get(
            "chicken_breed", chicken_breeds[0] if chicken_breeds else DEFAULT_CHICKEN_BREED
        )
        offset = request.query_params.get("offset", 0)

        # 初始載入資料
        batches = get_batch_data(
            chicken_breed, limit=DEFAULT_LIMIT_PLAIN, offset=int(offset), batch_name=batch_name if batch_name else None
        )

        return html_templates.TemplateResponse(
            "batches/plain.html",
            {
                "request": request,
                "batches": batches,
                "chicken_breeds": chicken_breeds,
                "chicken_breed": chicken_breed,
                "batch_name": batch_name,
                "has_more": len(batches) == DEFAULT_LIMIT_PLAIN,
                "next_offset": int(offset) + DEFAULT_LIMIT_PLAIN,
                "view": view,
            },
        )
    except Exception as e:
        logger.error(f"批次頁面錯誤: {e}")
        return html_templates.TemplateResponse("components/error.html", {"request": request, "error": str(e)})


@router.get("/sales", response_class=HTMLResponse)
async def sales(request: Request):
    """批次銷售資料頁面"""
    # print("sales", request.query_params)
    try:
        batch_name = request.query_params.get("batch_name", "")
        if not batch_name:
            return html_templates.TemplateResponse(
                "components/error.html", {"request": request, "error": "批次名稱為必填項目"}
            )

        # 獲取銷售數據
        sales_data = get_sales_data(batch_name)

        return html_templates.TemplateResponse(
            "batches/sales.html",
            {
                "request": request,
                "sales_data": sales_data,
                "batch_name": batch_name,
            },
        )
    except Exception as e:
        logger.error(f"銷售頁面錯誤: {e}")
        return html_templates.TemplateResponse("components/error.html", {"request": request, "error": str(e)})


@router.get("/feed", response_class=HTMLResponse)
async def feed(request: Request):
    """批次飼料資料頁面"""
    try:
        batch_name = request.query_params.get("batch_name", "")
        sub_location = request.query_params.get("sub_location", "")

        # 獲取飼料數據
        feed_data = get_feed_data(batch_name if batch_name else None, sub_location if sub_location else None)

        return html_templates.TemplateResponse(
            "batches/feed.html",
            {
                "request": request,
                "feed_data": feed_data,
                "batch_name": batch_name,
                "sub_location": sub_location,
            },
        )
    except Exception as e:
        logger.error(f"飼料頁面錯誤: {e}")
        return html_templates.TemplateResponse("components/error.html", {"request": request, "error": str(e)})


@router.get("/closure", response_class=HTMLResponse)
async def closure(request: Request):
    """批次結場資料頁面"""
    try:
        batch_name = request.query_params.get("batch_name", "")

        # 獲取結場數據
        production_data = get_farm_production_data(batch_name if batch_name else None)

        return html_templates.TemplateResponse(
            "batches/closure.html",
            {
                "request": request,
                "production_data": production_data,
                "batch_name": batch_name,
            },
        )
    except Exception as e:
        logger.error(f"結場頁面錯誤: {e}")
        return html_templates.TemplateResponse("components/error.html", {"request": request, "error": str(e)})


# @router.get("/", response_class=HTMLResponse)
# async def index(request: Request):
#     """批次摘要主頁面"""
#     try:
#         chicken_breeds = get_chicken_breeds()
#         chicken_breed = request.query_params.get(
#             "chicken_breed", chicken_breeds[0] if chicken_breeds else DEFAULT_CHICKEN_BREED
#         )
#         batch_name = request.query_params.get("batch_name", "")
#         offset = request.query_params.get("offset", 0)

#         # 初始載入資料
#         batches = get_batch_data(
#             chicken_breed, limit=DEFAULT_LIMIT_CARDS, offset=int(offset), batch_name=batch_name if batch_name else None
#         )

#         return html_templates.TemplateResponse(
#             "batches/index.html",
#             {
#                 "request": request,
#                 "batches": batches,
#                 "chicken_breeds": chicken_breeds,
#                 "chicken_breed": chicken_breed,
#                 "batch_name": batch_name,
#                 "has_more": len(batches) == DEFAULT_LIMIT_CARDS,
#                 "next_offset": int(offset) + DEFAULT_LIMIT_CARDS,
#                 "view": View.CARDS.value,
#             },
#         )
#     except Exception as e:
#         logger.error(f"批次頁面錯誤: {e}")
#         return html_templates.TemplateResponse("components/error.html", {"request": request, "error": str(e)})


# @router.get("/data", response_class=HTMLResponse)
# async def data(request: Request):
#     """批次資料端點 - 支援卡片和表格視圖"""
#     try:
#         chicken_breed = request.query_params.get("chicken_breed", DEFAULT_CHICKEN_BREED)
#         batch_name = request.query_params.get("batch_name", "")
#         view = request.query_params.get("view", "cards")
#         limit = int(request.query_params.get("limit", DEFAULT_LIMIT_CARDS))
#         offset = int(request.query_params.get("offset", 0))

#         batches = get_batch_data(chicken_breed, limit, offset, batch_name if batch_name else None)

#         match view:
#             case View.TABLE_ROWS.value:
#                 template_name = "batches/table.html"
#             case View.CARDS.value:
#                 template_name = "batches/cards.html"
#             case View.CARD_LIST.value:
#                 template_name = "batches/cards.html"
#             case View.TABLE.value:
#                 template_name = "batches/table.html"
#             case _:
#                 raise ValueError(f"Invalid view: {view}")
#         context = {
#             "request": request,
#             "batches": batches,
#             "chicken_breed": chicken_breed,
#             "batch_name": batch_name,
#             "has_more": len(batches) == limit,
#             "next_offset": offset + limit,
#             "view": view,
#         }

#         return html_templates.TemplateResponse(template_name, context)
#     except Exception as e:
#         logger.error(f"批次資料錯誤: {e}")
#         return html_templates.TemplateResponse("components/error.html", {"request": request, "error": str(e)})
