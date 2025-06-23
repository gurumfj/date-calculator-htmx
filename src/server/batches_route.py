import json
import logging
from datetime import datetime
from enum import Enum

import bleach
import markdown
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from todoist_api_python.api import TodoistAPI

from db_init import get_db_connection_context
from server.config import get_settings

from .todoist_service import TodoistCacheService, TodoService

logger = logging.getLogger(__name__)

router = APIRouter()
html_templates = Jinja2Templates(directory="src/server/templates")
sql_templates = Jinja2Templates(directory="src/server/templates/sql")

# Todoist service
todoist_token = get_settings().TODOIST_API_TOKEN
if not todoist_token:
    raise ValueError("TODOIST_API_TOKEN is not set")
todoist = TodoistAPI(todoist_token)

# 依賴注入
cache_service = TodoistCacheService()
todo_service = TodoService(todoist, cache_service)


# 添加千分位分隔符過濾器
def format_number(value):
    """格式化數字，添加千分位分隔符"""
    if value is None:
        return "0"
    return f"{int(value):,}"


# 添加Markdown過濾器
def markdown_to_html(value):
    """將Markdown文本轉換為HTML，包含安全清理"""
    if not value:
        return ""

    # 處理None和空值
    if value is None:
        return ""

    try:
        # 將值轉換為字符串並檢查長度限制
        text = str(value).strip()
        if not text:
            return ""

        # 限制文本長度以防止處理過大的內容
        if len(text) > 10000:  # 10KB限制
            text = text[:10000] + "... (內容已截斷)"
            logger.warning("Markdown content truncated due to length limit")

        # 創建Markdown實例，啟用安全擴展
        md = markdown.Markdown(
            extensions=[
                "markdown.extensions.nl2br",  # 換行轉換
                "markdown.extensions.fenced_code",  # 代碼塊
                "markdown.extensions.tables",  # 表格
                "markdown.extensions.codehilite",  # 代碼高亮
            ],
            extension_configs={
                "codehilite": {
                    "css_class": "highlight",
                    "use_pygments": False,  # 不使用Pygments，使用CSS類
                }
            },
        )

        # 轉換Markdown為HTML
        html = md.convert(text)

        # 使用bleach清理HTML，只允許安全的標籤和屬性
        allowed_tags = [
            "p",
            "br",
            "strong",
            "em",
            "u",
            "i",
            "b",
            "h1",
            "h2",
            "h3",
            "h4",
            "h5",
            "h6",
            "ul",
            "ol",
            "li",
            "blockquote",
            "code",
            "pre",
            "table",
            "thead",
            "tbody",
            "tr",
            "th",
            "td",
            "a",
        ]

        allowed_attributes = {
            "a": ["href", "title"],
            "code": ["class"],
            "pre": ["class"],
            "*": ["class"],  # 允許class屬性用於樣式
        }

        # 清理HTML
        clean_html = bleach.clean(html, tags=allowed_tags, attributes=allowed_attributes, strip=True)

        return clean_html

    except Exception as e:
        logger.error(f"Error converting markdown to HTML: {e}")
        # 如果轉換失敗，返回原始文本但進行HTML轉義
        escaped_text = str(value).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        return f"<p>{escaped_text}</p>"


html_templates.env.filters["format_number"] = format_number
html_templates.env.filters["markdown_to_html"] = markdown_to_html


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
DEFAULT_LIMIT_PLAIN = 30


def get_batch_data(chicken_breed: str, limit: int = 50, offset: int = 0, batch_name: str | None = None):
    """共用的資料獲取邏輯"""
    with get_db_connection_context() as conn:
        # 渲染SQL模板
        sql_query = sql_templates.get_template("batch_summary.sql").render(batch_name=batch_name)

        # 準備查詢參數
        params = {"chicken_breed": chicken_breed, "limit": limit, "offset": offset}

        # 如果有批次名稱搜尋，加入LIKE參數
        if batch_name:
            params["batch_name"] = f"%{batch_name}%"

        # 執行查詢
        rows = conn.execute(sql_query, params).fetchall()

        batches = []
        for row in rows:
            batch = dict(row)
            # 解析breed_details JSON
            if batch.get("breed_details"):
                try:
                    batch["breed_details"] = json.loads(batch["breed_details"])
                except (json.JSONDecodeError, TypeError):
                    batch["breed_details"] = []
            batches.append(batch)

        return batches


def get_chicken_breeds():
    """取得所有雞種"""
    with get_db_connection_context() as conn:
        rows = conn.execute("SELECT DISTINCT chicken_breed FROM breed ORDER BY chicken_breed").fetchall()
        chicken_breeds = [row[0] for row in rows]
        return chicken_breeds


def get_sales_data(batch_name: str, sale_date: str | None = None):
    """獲取特定批次的銷售數據"""
    with get_db_connection_context() as conn:
        # 渲染SQL模板
        sql_query = sql_templates.get_template("sales.sql").render(sale_date=sale_date)

        # 準備查詢參數 - 總是包含所有必需的參數
        params = {
            "batch_name": batch_name,
            "sale_date": sale_date,  # 即使是 None 也要提供
        }

        # 執行查詢
        rows = conn.execute(sql_query, params).fetchall()

        sales_data = []
        for row in rows:
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

        return sales_data


def get_feed_data(batch_name: str | None = None, sub_location: str | None = None):
    """獲取飼料數據"""
    with get_db_connection_context() as conn:
        # 渲染SQL模板
        sql_query = sql_templates.get_template("feed.sql").render(batch_name=batch_name, sub_location=sub_location)

        # 準備查詢參數
        params = {}
        if batch_name:
            params["batch_name"] = batch_name
        if sub_location:
            params["sub_location"] = sub_location

        # 執行查詢
        rows = conn.execute(sql_query, params).fetchall()

        feed_data = []
        for row in rows:
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

        return feed_data


def get_farm_production_data(batch_name: str | None = None):
    """獲取農場生產結場數據"""
    with get_db_connection_context() as conn:
        # 渲染SQL模板
        sql_query = sql_templates.get_template("farm_production.sql").render(batch_name=batch_name)

        # 準備查詢參數
        params = {}
        if batch_name:
            params["batch_name"] = batch_name

        # 執行查詢
        rows = conn.execute(sql_query, params).fetchall()

        production_data = []
        for row in rows:
            production_record = dict(row)

            # 處理日期格式
            if production_record.get("created_at"):
                production_record["created_at"] = production_record["created_at"].split("T")[0]

            production_data.append(production_record)

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
    try:
        batch_name = request.query_params.get("batch_name", "")
        if not batch_name:
            return html_templates.TemplateResponse(
                "components/error.html", {"request": request, "error": "批次名稱為必填項目"}
            )

        # 獲取銷售數據
        sales_data = get_sales_data(batch_name)

        content = html_templates.get_template("batches/sales.html").render(sales_data=sales_data)

        if request.headers.get("HX-Request"):
            return content

        return html_templates.TemplateResponse(
            "batches/base.html",
            {
                "request": request,
                "tab": "sales",
                "title": batch_name,
                "content": content,
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
        if not batch_name:
            return html_templates.TemplateResponse(
                "components/error.html", {"request": request, "error": "批次名稱為必填項目"}
            )
        # sub_location = request.query_params.get("sub_location", "")

        # 獲取飼料數據
        feed_data = get_feed_data(batch_name if batch_name else None)

        content = html_templates.get_template("batches/feed.html").render(feed_data=feed_data)

        if request.headers.get("HX-Request"):
            return content

        return html_templates.TemplateResponse(
            "batches/base.html",
            {
                "request": request,
                "tab": "feed",
                "title": batch_name,
                "content": content,
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
        if not batch_name:
            return html_templates.TemplateResponse(
                "components/error.html", {"request": request, "error": "批次名稱為必填項目"}
            )

        # 獲取結場數據
        production_data = get_farm_production_data(batch_name)

        content = html_templates.get_template("batches/closure.html").render(production_data=production_data)

        if request.headers.get("HX-Request"):
            return content

        return html_templates.TemplateResponse(
            "batches/base.html",
            {
                "request": request,
                "tab": "closure",
                "title": batch_name,
                "content": content,
            },
        )
    except Exception as e:
        logger.error(f"結場頁面錯誤: {e}")
        return html_templates.TemplateResponse("components/error.html", {"request": request, "error": str(e)})


@router.get("/article", response_class=HTMLResponse)
async def article(request: Request):
    """批次記事頁面（Todoist任務）"""
    try:
        batch_name = request.query_params.get("batch_name", "")
        if not batch_name:
            return html_templates.TemplateResponse(
                "components/error.html", {"request": request, "error": "批次名稱為必填項目"}
            )

        breed_query_stmt = """
            SELECT
                batch_name,
                breed_date as since,
                date(breed_date, "+140 days") as until
            FROM
                breed
            WHERE
                batch_name = :batch_name
            order by breed_date
        """

        with get_db_connection_context() as conn:
            breed_data = conn.execute(breed_query_stmt, {"batch_name": batch_name}).fetchone()

        if not breed_data:
            return html_templates.TemplateResponse(
                "components/error.html", {"request": request, "error": "找不到指定的批次"}
            )
        breed_data = dict(breed_data)
        since_datetime = datetime.strptime(breed_data["since"], "%Y-%m-%d")
        until_datetime = datetime.strptime(breed_data["until"], "%Y-%m-%d")

        # 直接渲染基礎模板，任務將通過 HTMX 按需加載
        content = html_templates.get_template("batches/article.html").render(batch_name=batch_name)

        if request.headers.get("HX-Request"):
            return content

        return html_templates.TemplateResponse(
            "batches/base.html",
            {
                "request": request,
                "tab": "article",
                "title": batch_name,
                "content": content,
            },
        )
    except Exception as e:
        logger.error(f"記事頁面錯誤: {e}")
        return html_templates.TemplateResponse("components/error.html", {"request": request, "error": str(e)})


@router.get("/breed", response_class=HTMLResponse)
async def breed(request: Request):
    """批次操作 modal 內容"""
    try:
        batch_name = request.query_params.get("batch_name", "")
        if not batch_name:
            return html_templates.TemplateResponse(
                "components/error.html", {"request": request, "error": "批次名稱為必填項目"}
            )

        # 獲取批次資料
        batches = get_batch_data("", limit=1, offset=0, batch_name=batch_name)
        if not batches:
            return html_templates.TemplateResponse(
                "components/error.html", {"request": request, "error": "找不到指定的批次"}
            )
        batch = batches[0]

        content = html_templates.get_template("batches/breed.html").render(batch=batch)

        if request.headers.get("HX-Request"):
            return content

        return html_templates.TemplateResponse(
            "batches/base.html",
            {
                "request": request,
                "tab": "breed",
                "title": batch.get("batch_name", ""),
                "content": content,
            },
        )
    except Exception as e:
        logger.error(f"批次操作錯誤: {e}")
        return html_templates.TemplateResponse("components/error.html", {"request": request, "error": str(e)})


@router.get("/article/active-tasks", response_class=HTMLResponse)
async def article_active_tasks(request: Request):
    """快速加載活動任務"""
    try:
        batch_name = request.query_params.get("batch_name", "")
        if not batch_name:
            return html_templates.TemplateResponse(
                "components/error.html", {"request": request, "error": "批次名稱為必填項目"}
            )

        # 獲取活動任務（快）
        # force_refresh = request.query_params.get("refresh", "false").lower() == "false"
        active_tasks = todo_service.get_active_tasks_with_cache(batch_name, force_refresh=False)

        # 按到期日排序
        sorted_tasks = sorted(active_tasks, key=lambda x: x.get("due_date") or "1970-01-01", reverse=True)

        return html_templates.get_template("batches/article_tasks.html").render(
            tasks=sorted_tasks, batch_name=batch_name, task_type="active", section_title="活動任務"
        )
    except Exception as e:
        logger.error(f"獲取活動任務錯誤: {e}")
        return html_templates.TemplateResponse("components/error.html", {"request": request, "error": str(e)})


@router.get("/article/completed-tasks", response_class=HTMLResponse)
async def article_completed_tasks(request: Request):
    """加載已完成任務"""
    try:
        batch_name = request.query_params.get("batch_name", "")
        if not batch_name:
            return html_templates.TemplateResponse(
                "components/error.html", {"request": request, "error": "批次名稱為必填項目"}
            )

        # 獲取批次時間範圍
        breed_query_stmt = """
            SELECT
                batch_name,
                breed_date as since,
                date(breed_date, "+140 days") as until
            FROM
                breed
            WHERE
                batch_name = :batch_name
            order by breed_date
        """

        with get_db_connection_context() as conn:
            breed_data = conn.execute(breed_query_stmt, {"batch_name": batch_name}).fetchone()

        if not breed_data:
            return html_templates.TemplateResponse(
                "components/error.html", {"request": request, "error": "找不到指定的批次"}
            )

        breed_data = dict(breed_data)
        since_datetime = datetime.strptime(breed_data["since"], "%Y-%m-%d")
        until_datetime = datetime.strptime(breed_data["until"], "%Y-%m-%d")

        # 獲取已完成任務（慢）
        # force_refresh = request.query_params.get("refresh", "false").lower() == "false"
        completed_tasks = todo_service.get_completed_tasks_with_cache(
            batch_name, since=since_datetime, until=until_datetime, force_refresh=False
        )

        # 按到期日排序
        sorted_tasks = sorted(completed_tasks, key=lambda x: x.get("due_date") or "1970-01-01", reverse=True)

        return html_templates.get_template("batches/article_tasks.html").render(
            tasks=sorted_tasks, batch_name=batch_name, task_type="completed", section_title="已完成任務"
        )
    except Exception as e:
        logger.error(f"獲取已完成任務錯誤: {e}")
        return html_templates.TemplateResponse("components/error.html", {"request": request, "error": str(e)})


@router.delete("/todo/delete/{task_id}")
async def delete_task(task_id: str):
    try:
        success = todo_service.delete_task(task_id)
        if success:
            return JSONResponse(status_code=200, content={"message": "Task deleted successfully"})
        else:
            return JSONResponse(status_code=500, content={"error": "Failed to delete task"})
    except Exception as e:
        logger.error(f"刪除任務錯誤: {e}")
        return JSONResponse(status_code=500, content={"error": str(e)})


@router.post("/todo/complete/{task_id}")
async def complete_task(task_id: str, request: Request):
    try:
        success = todo_service.complete_task(task_id)
        if success:
            # 對於 HTMX 請求，返回空內容以移除該行，並觸發事件刷新已完成任務區域
            if request.headers.get("HX-Request"):
                response = HTMLResponse("")
                response.headers["HX-Trigger"] = "taskCompleted"
                return response
            return JSONResponse(status_code=200, content={"message": "Task completed successfully"})
        else:
            return JSONResponse(status_code=500, content={"error": "Failed to complete task"})
    except Exception as e:
        logger.error(f"完成任務錯誤: {e}")
        return JSONResponse(status_code=500, content={"error": str(e)})


@router.post("/todo/uncomplete/{task_id}")
async def uncomplete_task(task_id: str, request: Request):
    try:
        success = todo_service.uncomplete_task(task_id)
        if success:
            # 對於 HTMX 請求，返回空內容以移除該行，並觸發事件刷新活動任務區域
            if request.headers.get("HX-Request"):
                response = HTMLResponse("")
                response.headers["HX-Trigger"] = "taskUncompleted"
                return response
            return JSONResponse(status_code=200, content={"message": "Task uncompleted successfully"})
        else:
            return JSONResponse(status_code=500, content={"error": "Failed to uncomplete task"})
    except Exception as e:
        logger.error(f"取消完成任務錯誤: {e}")
        return JSONResponse(status_code=500, content={"error": str(e)})
