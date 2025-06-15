import logging

import pandas as pd
from fastapi import FastAPI, Request, UploadFile, File, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

from cleansales_backend.commands.upload_commands import UploadFileCommand
from cleansales_backend.handlers.upload_handler import UploadCommandHandler
from cleansales_backend.queries.data_queries import (
    DataQueryHandler,
    GetDataQuery,
    GetEventDetailsQuery,
    GetUploadEventsQuery,
    PaginationQuery,
)
from cleansales_backend.database.init import init_db

logger = logging.getLogger(__name__)
DB_PATH = "./data/sqlite.db"

init_db()

app = FastAPI(title="Cleansales Upload Helper")

# Setup Jinja2 templates
templates = Jinja2Templates(directory="src/server/templates")

# Setup static files
app.mount("/static", StaticFiles(directory="src/cleansales_backend/web/static"), name="static")

upload_handler = UploadCommandHandler(DB_PATH)
data_query_handler = DataQueryHandler(DB_PATH)




async def get_tab_content(request: Request, tab: str):
    """直接獲取標籤頁內容"""
    if tab == "upload":
        return templates.TemplateResponse("components/upload_form.html", {"request": request})
    elif tab == "events":
        return await view_upload_events(request)
    elif tab in ["breeds", "sales", "feeds", "farm_production"]:
        # 直接調用數據查詢
        table_name = "breed" if tab == "breeds" else ("sale" if tab == "sales" else ("feed" if tab == "feeds" else "farm_production"))
        return await query_data_html(request, table_name)
    elif tab == "sql":
        return templates.TemplateResponse("components/sql_form.html", {"request": request})
    
    return templates.TemplateResponse("components/upload_form.html", {"request": request})




@app.get("/", response_class=HTMLResponse)
async def index(request: Request, tab: str = "upload"):
    """主頁面"""
    return templates.TemplateResponse("index.html", {
        "request": request, 
        "tab": tab
    })


@app.get("/tab/{tab}", response_class=HTMLResponse)
async def get_tab(request: Request, tab: str):
    # 如果不是 HTMX 請求，返回完整頁面
    if not request.headers.get("HX-Request") == "true":
        return await index(request, tab)
    # time.sleep(3)

    # 如果是 HTMX 請求，直接返回內容
    return await get_tab_content(request, tab)


@app.post("/upload", response_class=HTMLResponse)
async def upload_file(request: Request, file: UploadFile = File(...)):
    """文件上傳處理"""
    command = UploadFileCommand(file=file)
    result = await upload_handler.handle(command)
    
    if result["success"]:
        # 獲取上傳結果數據
        query = GetDataQuery(table_name=result["file_type"])
        data_list, _ = data_query_handler.handle_get_data_query(query)
        df = pd.DataFrame(data_list)
        
        # 渲染表格為字符串
        table_template = templates.get_template("components/table.html")
        table_html = table_template.render(
            df=df,
            table=result["file_type"],
            sort_by_column=None,
            sort_order="DESC",
            page=0,
            page_size=50,
            has_more=False,
            enable_event_links=False,
            request=request
        )
        
        context = {
            "request": request,
            "success": True,
            "result": result,
            "table_html": table_html
        }
    else:
        context = {
            "request": request,
            "success": False,
            "result": result
        }
    
    return templates.TemplateResponse("components/upload_result.html", context)


@app.get("/events", response_class=HTMLResponse)
async def view_upload_events(request: Request):
    """查看上傳事件歷史"""
    query = GetUploadEventsQuery(limit=100)
    data = data_query_handler.handle_get_upload_events_query(query)
    
    if not data:
        return HTMLResponse(content="<p>目前沒有上傳記錄</p>")
    
    df = pd.DataFrame(data)
    
    # 格式化顯示
    if 'upload_timestamp' in df.columns:
        df['upload_timestamp'] = pd.to_datetime(df['upload_timestamp']).dt.strftime('%Y-%m-%d %H:%M:%S')
    if 'file_size' in df.columns:
        df['file_size'] = df['file_size'].apply(lambda x: f"{x/1024:.1f} KB" if x else "0 KB")
    if 'processing_time_ms' in df.columns:
        df['processing_time_ms'] = df['processing_time_ms'].apply(lambda x: f"{x} ms" if x else "0 ms")
    
    context = {
        "request": request,
        "df": df,
        "table": "events",
        "sort_by_column": "upload_timestamp",
        "sort_order": "DESC",
        "page": 0,
        "page_size": 100,
        "has_more": False,
        "enable_event_links": True
    }
    
    return templates.TemplateResponse("components/table.html", context)


@app.get("/q/{table}", response_class=HTMLResponse)
async def query_data_html(request: Request, table: str, sort_by_column: str | None = None, 
                         sort_order: str | None = None, page: int = 0, page_size: int = 50, 
                         event_id: str | None = None):
    """查詢數據並返回HTML"""
    query = GetDataQuery(
        table_name=table, 
        sort_by_column=sort_by_column, 
        sort_order=sort_order,
        pagination=PaginationQuery(page=page+1, page_size=page_size), 
        event_id=event_id
    )
    data, total_pages = data_query_handler.handle_get_data_query(query)
    
    df = pd.DataFrame(data)
    has_more = (page + 1) < total_pages
    
    # 準備模板上下文
    context = {
        "request": request,
        "df": df,
        "table": table,
        "sort_by_column": sort_by_column,
        "sort_order": sort_order or "DESC",
        "page": page,
        "page_size": page_size,
        "has_more": has_more,
        "enable_event_links": table == "events"
    }
    
    if page == 0:
        # 第一頁返回完整表格
        return templates.TemplateResponse("components/table.html", context)
    else:
        # 後續頁面只返回行
        return templates.TemplateResponse("components/table_rows.html", context)




@app.get("/event/{event_id}", response_class=HTMLResponse)
async def view_event_records(request: Request, event_id: str):
    """查看特定事件的數據記錄"""
    try:
        # 獲取事件信息
        event_query = GetEventDetailsQuery(event_id=event_id)
        event_dict = data_query_handler.handle_get_event_details_query(event_query)
        
        if not event_dict:
            context = {
                "request": request,
                "error": f"找不到事件 ID: {event_id}",
                "event_id": event_id
            }
            return templates.TemplateResponse("components/event_error.html", context)
        
        file_type = event_dict['file_type']
        
        # 根據文件類型查詢對應的數據表
        table_map = {
            'breed': 'breed',
            'sale': 'sale',
            'feed': 'feed',
            'farm_production': 'farm_production'
        }
        
        if file_type not in table_map:
            context = {
                "request": request,
                "error": f"不支持的文件類型: {file_type}",
                "event_id": event_id
            }
            return templates.TemplateResponse("components/event_error.html", context)
        
        table_name = table_map[file_type]
        
        # 查詢該事件的所有記錄
        data_query = GetDataQuery(
            table_name=table_name, 
            event_id=event_id, 
            pagination=PaginationQuery(page=1, page_size=100)
        )
        data_records, _ = data_query_handler.handle_get_data_query(data_query)
        
        table_html = ""
        if data_records:
            df = pd.DataFrame(data_records)
            
            # 移除event_id欄位以避免重複顯示
            if 'event_id' in df.columns:
                df = df.drop('event_id', axis=1)
            
            # 渲染表格
            table_template = templates.get_template("components/table.html")
            table_html = table_template.render(
                df=df,
                table=file_type,
                sort_by_column=None,
                sort_order="DESC",
                page=0,
                page_size=100,
                has_more=False,
                enable_event_links=False,
                request=request
            )
        
        context = {
            "request": request,
            "event": event_dict,
            "event_id": event_id,
            "table_html": table_html,
            "data_count": len(data_records) if data_records else 0
        }
        
        return templates.TemplateResponse("components/event_detail.html", context)
        
    except Exception as e:
        context = {
            "request": request,
            "error": f"查詢事件記錄失敗: {str(e)}",
            "event_id": event_id
        }
        return templates.TemplateResponse("components/event_error.html", context)


@app.post("/sql", response_class=HTMLResponse)
async def execute_sql(request: Request, sql: str = Form(...)):
    """執行自定義SQL查詢"""
    if not sql.strip():
        return HTMLResponse(content='<div style="color: red;">請輸入SQL查詢語句</div>')
    
    # 基本的SQL安全檢查
    sql_lower = sql.lower().strip()
    if not sql_lower.startswith(('select', 'with')):
        return HTMLResponse(content='<div style="color: red;">只允許SELECT和WITH查詢語句</div>')
    
    # 檢查是否包含危險操作
    dangerous_keywords = ['drop', 'delete', 'update', 'insert', 'alter', 'create', 'truncate']
    if any(keyword in sql_lower for keyword in dangerous_keywords):
        return HTMLResponse(content='<div style="color: red;">不允許包含修改數據的SQL語句</div>')
    
    # 強制添加LIMIT語句
    if 'limit' not in sql_lower:
        sql = sql.rstrip(';') + ' LIMIT 1000'
    
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
            page=0,
            page_size=50,
            has_more=False,
            enable_event_links=False,
            request=request
        )
        result_html = f'<p>查詢成功，共 {len(results)} 筆結果</p>{table_html}'
        
        return HTMLResponse(content=result_html)
        
    except Exception as e:
        return HTMLResponse(content=f'<div style="color: red;">SQL執行錯誤: {str(e)}</div>')
    finally:
        conn.close()


# API endpoints (for compatibility)
@app.post("/api/upload")
async def api_upload(file: UploadFile = File(...)):
    """API上傳路由，返回JSON格式"""
    command = UploadFileCommand(file=file)
    return await upload_handler.handle(command)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server.main:app", host="0.0.0.0", port=8000, reload=True)