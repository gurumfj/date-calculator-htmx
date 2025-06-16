import logging

import pandas as pd
from fastapi import APIRouter, File, Form, Request, UploadFile
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from cleansales_backend.commands.upload_commands import UploadFileCommand
from cleansales_backend.database.init import init_db
from cleansales_backend.handlers.upload_handler import UploadCommandHandler
from cleansales_backend.queries.data_queries import (
    DataQueryHandler,
    GetDataQuery,
    GetEventDetailsQuery,
    GetUploadEventsQuery,
    PaginationQuery,
)

logger = logging.getLogger(__name__)
DB_PATH = "./data/sqlite.db"

init_db()

# Create upload router
router = APIRouter()

# Setup Jinja2 templates
templates = Jinja2Templates(directory="src/server/templates")

# Note: Static files will be mounted in main.py

upload_handler = UploadCommandHandler(DB_PATH)
data_query_handler = DataQueryHandler(DB_PATH)


async def get_tab_content(request: Request, tab: str):
    """直接獲取標籤頁內容"""
    if tab == "upload":
        return templates.TemplateResponse("uploader/components/upload_form.html", {"request": request})
    elif tab == "events":
        return await view_upload_events(request)
    elif tab in ["breeds", "sales", "feeds", "farm_production"]:
        # 直接調用數據查詢
        table_name = (
            "breed"
            if tab == "breeds"
            else ("sale" if tab == "sales" else ("feed" if tab == "feeds" else "farm_production"))
        )
        return await query_table(request, table_name)
    elif tab == "sql":
        return templates.TemplateResponse("components/sql_form.html", {"request": request})

    return templates.TemplateResponse("components/upload_form.html", {"request": request})


# 全局常量，避免重複創建
NAV_ITEMS = [
    {"title": "Upload", "value": "upload", "href": "upload"},
    {"title": "Events", "value": "events", "href": "events"},
    {"title": "Breeds", "value": "breeds", "href": "breeds"},
    {"title": "Sales", "value": "sales", "href": "sales"},
    {"title": "Feeds", "value": "feeds", "href": "feeds"},
    {"title": "Farm Production", "value": "farm_production", "href": "farm_production"},
    {"title": "SQL", "value": "sql", "href": "sql"},
]


@router.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """主頁面重定向到 upload"""
    return await get_tab(request, "upload")


@router.get("/{tab}", response_class=HTMLResponse)
async def get_tab(request: Request, tab: str):
    """獲取標籤頁內容"""
    # 檢查 tab 是否在有效的導航項目中
    valid_tabs = [item["value"] for item in NAV_ITEMS]
    if tab not in valid_tabs:
        # 如果是直接瀏覽器訪問無效 tab，重定向到 upload
        if not request.headers.get("HX-Request") == "true":
            return RedirectResponse(url="upload", status_code=302)
        # 如果是 HTMX 請求，返回 404 內容
        else:
            return HTMLResponse(content="<div>頁面不存在</div>", status_code=404)

    # 如果不是 HTMX 請求，返回完整頁面
    if not request.headers.get("HX-Request") == "true":
        return templates.TemplateResponse(
            "uploader/index.html", {"request": request, "tab": tab, "nav_items": NAV_ITEMS, "active_tab": tab}
        )

    # HTMX 請求，直接返回內容
    match tab:
        case "upload":
            return templates.TemplateResponse("uploader/components/upload_form.html", {"request": request})
        case "events":
            return await view_upload_events(request)
        case "breeds" | "sales" | "feeds" | "farm_production":
            # 直接調用數據查詢
            table_name = (
                "breed"
                if tab == "breeds"
                else ("sale" if tab == "sales" else ("feed" if tab == "feeds" else "farm_production"))
            )
            return await query_table(request, table_name)
        case "sql":
            return templates.TemplateResponse("uploader/components/sql_form.html", {"request": request})
        case _:
            return templates.TemplateResponse("uploader/components/upload_form.html", {"request": request})


@router.post("/upload", response_class=HTMLResponse)
async def upload_file(request: Request, file: UploadFile = File(...)):
    """文件上傳處理"""
    command = UploadFileCommand(file=file)
    result = await upload_handler.handle(command)

    if result.success:
        # 直接使用 UploadResult.data 中的資料庫資料
        df = pd.DataFrame(result.data)

        # 渲染表格為字符串 - Controller 決定渲染邏輯
        context = {
            "request": request,
            "df": df,
            "table": result.file_type,
            "sort_by_column": None,
            "sort_order": "DESC",
            "enable_event_links": False,
            "render_type": "empty" if df.empty else "full",
        }

        table_html = templates.get_template("components/table.html").render(**context)

        context = {"request": request, "success": True, "result": result.to_dict(), "table_html": table_html}
    else:
        context = {"request": request, "success": False, "result": result.to_dict()}

    return templates.TemplateResponse("uploader/components/upload_result.html", context)


@router.get("/events", response_class=HTMLResponse)
async def view_upload_events(request: Request):
    """查看上傳事件歷史"""
    query = GetUploadEventsQuery(limit=100)
    data = data_query_handler.handle_get_upload_events_query(query)

    if not data:
        return HTMLResponse(content="<p>目前沒有上傳記錄</p>")

    df = pd.DataFrame(data)

    # 格式化顯示
    if "upload_timestamp" in df.columns:
        df["upload_timestamp"] = pd.to_datetime(df["upload_timestamp"]).dt.strftime("%Y-%m-%d %H:%M:%S")
    if "file_size" in df.columns:
        df["file_size"] = df["file_size"].apply(lambda x: f"{x / 1024:.1f} KB" if x else "0 KB")
    if "processing_time_ms" in df.columns:
        df["processing_time_ms"] = df["processing_time_ms"].apply(lambda x: f"{x} ms" if x else "0 ms")

    # Controller 決定渲染邏輯
    context = {
        "request": request,
        "df": df,
        "table": "events",
        "sort_by_column": "upload_timestamp",
        "sort_order": "DESC",
        "enable_event_links": True,
        "render_type": "empty" if df.empty else "full",
    }

    return templates.TemplateResponse("components/table.html", context)


# Helper function to render table responses
def _render_table_response(
    request: Request,
    df: pd.DataFrame,
    table_name: str,
    column: str | None,
    current_sort_order: str | None,
    page: int,
    has_more: bool,
    templates: Jinja2Templates,
    html_output: bool = False,
) -> HTMLResponse | str:
    """根據查詢結果和分頁信息渲染表格模板。"""
    # Determine the sort order for template links (toggling sort)
    # If current_sort_order is DESC, link should offer ASC. If ASC, link offers DESC.
    template_link_sort_order = "ASC" if current_sort_order == "DESC" else "DESC"

    base_context = {
        "request": request,
        "df": df,
        "table": table_name,
        "enable_event_links": table_name == "events",
        "sort_by_column": column,
        "sort_order": template_link_sort_order,  # For template links
        "this_page": page,
        "has_more": has_more,
    }
    table_template = templates.get_template("components/table.html").render(**base_context)

    if df.empty:
        # For empty df, still render the table structure (headers)
        return (
            templates.TemplateResponse("components/table.html", context=base_context)
            if not html_output
            else table_template
        )

    if page == 1:
        # First page: render the full table structure
        return (
            templates.TemplateResponse("components/table.html", context=base_context)
            if not html_output
            else table_template
        )
    else:
        # Subsequent pages: render only the row content for HTMX
        return (
            templates.TemplateResponse("components/_table_rows_content.html", context=base_context)
            if not html_output
            else table_template
        )


@router.get("/q/{table}/{order}/{page}", response_class=HTMLResponse)
async def query_table(
    request: Request,
    table: str,
    column: str | None = None,
    order: str | None = None,
    page: int = 1,
    page_size: int = 50,
    event_id: str | None = None,
):
    """查詢數據並返回HTML"""
    query = GetDataQuery(
        table_name=table,
        sort_by_column=None if column == "None" else column,
        sort_order=order,
        pagination=PaginationQuery(page=page, page_size=page_size),
        event_id=event_id,
    )
    data, total_pages = data_query_handler.handle_get_data_query(query)

    df = pd.DataFrame(data)
    has_more = (page + 1) < total_pages
    next_page: int = page + 1 if has_more else 0
    print(f"page={page}, total_pages={total_pages}, has_more={has_more}, next_page={next_page}")

    return _render_table_response(
        request=request,
        df=df,
        table_name=table,
        column=column,
        current_sort_order=order,
        page=page,
        has_more=has_more,
        templates=templates,
        html_output=False,
    )


@router.get("/event/{event_id}", response_class=HTMLResponse)
async def view_event_records(request: Request, event_id: str):
    """查看特定事件的數據記錄"""
    try:
        # 獲取事件信息
        event_query = GetEventDetailsQuery(event_id=event_id)
        event_dict = data_query_handler.handle_get_event_details_query(event_query)

        if not event_dict:
            context = {"request": request, "error": f"找不到事件 ID: {event_id}", "event_id": event_id}
            return templates.TemplateResponse("uploader/components/event_error.html", context)

        file_type = event_dict["file_type"]

        # 根據文件類型查詢對應的數據表
        table_map = {"breed": "breed", "sale": "sale", "feed": "feed", "farm_production": "farm_production"}

        if file_type not in table_map:
            context = {"request": request, "error": f"不支持的文件類型: {file_type}", "event_id": event_id}
            return templates.TemplateResponse("uploader/components/event_error.html", context)

        table_name = table_map[file_type]

        # 查詢該事件的所有記錄
        data_query = GetDataQuery(
            table_name=table_name, event_id=event_id, pagination=PaginationQuery(page=1, page_size=100)
        )
        data_records, total_pages = data_query_handler.handle_get_data_query(data_query)

        if not data_records:
            df = pd.DataFrame()
        else:
            df = pd.DataFrame(data_records).drop(columns=["event_id"])

        table_html = _render_table_response(
            request=request,
            df=df,
            table_name=table_name,
            column=None,
            current_sort_order="DESC",
            page=1,
            has_more=False if total_pages == 1 else True,
            templates=templates,
            html_output=True,
        )

        context = {
            "request": request,
            "table": table_name,
            "event": event_dict,
            "event_id": event_id,
            "table_html": table_html,
            "data_count": len(data_records) if data_records else 0,
        }

        return templates.TemplateResponse("uploader/components/event_detail.html", context)

    except Exception as e:
        context = {"request": request, "error": f"查詢事件記錄失敗: {str(e)}", "event_id": event_id}
        return templates.TemplateResponse("uploader/components/event_error.html", context)


@router.post("/sql", response_class=HTMLResponse)
async def execute_sql(request: Request, sql: str = Form(...)):
    """執行自定義SQL查詢"""
    if not sql.strip():
        return HTMLResponse(content='<div style="color: red;">請輸入SQL查詢語句</div>')

    # 基本的SQL安全檢查
    sql_lower = sql.lower().strip()
    if not sql_lower.startswith(("select", "with")):
        return HTMLResponse(content='<div style="color: red;">只允許SELECT和WITH查詢語句</div>')

    # 檢查是否包含危險操作
    dangerous_keywords = ["drop", "delete", "update", "insert", "alter", "create", "truncate"]
    if any(keyword in sql_lower for keyword in dangerous_keywords):
        return HTMLResponse(content='<div style="color: red;">不允許包含修改數據的SQL語句</div>')

    # 強制添加LIMIT語句
    if "limit" not in sql_lower:
        sql = sql.rstrip(";") + " LIMIT 1000"

    conn = data_query_handler.get_db_connection()
    try:
        cursor = conn.execute(sql)
        results = cursor.fetchall()

        if not results:
            return HTMLResponse(content="<div>查詢無結果</div>")

        # 將結果轉換為DataFrame
        data = [dict(row) for row in results]
        df = pd.DataFrame(data)

        # 渲染表格
        table_template = templates.get_template("components/table.html")
        table_html = table_template.render(
            df=df,
            table="sql",
            sort_by_column=None,
            sort_order="DESC",
            render_head=True,
            render_load_more=False,
            enable_event_links=False,
            request=request,
        )
        result_html = f"<p>查詢成功，共 {len(results)} 筆結果</p>{table_html}"

        return HTMLResponse(content=result_html)

    except Exception as e:
        return HTMLResponse(content=f'<div style="color: red;">SQL執行錯誤: {str(e)}</div>')
    finally:
        conn.close()


# This router will be included in main.py
