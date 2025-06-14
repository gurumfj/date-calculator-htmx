import json
import logging
import pandas as pd

from cleansales_backend.core.config import get_settings
from fasthtml.common import *
from cleansales_backend.web.resources import alpine_cdn
from cleansales_backend.commands.upload_commands import UploadFileCommand
from cleansales_backend.handlers.upload_handler import UploadCommandHandler
from cleansales_backend.queries.data_queries import DataQueryHandler, GetDataQuery, GetUploadEventsQuery, GetEventDetailsQuery, PaginationQuery

logger = logging.getLogger(__name__)
DB_PATH = "./data/sqlite.db"

from cleansales_backend.database.init import init_db
init_db()

upload_handler = UploadCommandHandler(DB_PATH)
data_query_handler = DataQueryHandler(DB_PATH)

app, rt = fast_app(
    live=get_settings().WEB_LIVE,
    key_fname=".sesskey",
    session_cookie="cleansales",
    max_age=86400,
    static_path='static',
    surreal=False,
    hdrs=(alpine_cdn,))

upload_breeds_form = Form(
    Label("Upload Files", Input(type="file", name="file", accept=".xlsx, .xls")),
    Button("Upload", type="submit"),
    enctype="multipart/form-data",
    hx_post="/upload",
    hx_target="#result",
    hx_push="true",
    hx_success="alert('Upload successful!')",
)

sql_query_form = Form(
    Label("SQL Query", 
          Textarea(name="sql", placeholder="輸入SQL查詢語句...", rows=3, cols=50, style="width: 100%;")),
    Button("Execute", type="submit"),
    hx_post="/sql",
    hx_target="#result",
    hx_trigger="keyup delay:500ms",
    hx_push="true",
)

def render_table(df: pd.DataFrame, table: str, sort_by_column: str | None = None, sort_order: str = "DESC", page: int = 0, page_size: int = 50, total_pages:int = -1, enable_event_links: bool = False,):
    headers = df.columns
    
    # 不在這裡分頁，數據已經在query中分頁了
    rows = df.values
    
    def create_header(header):
        # 決定下一次點擊的排序方向
        next_order = "ASC" if sort_by_column == header and sort_order == "DESC" else "DESC"
        
        # 顯示排序指示器
        indicator = ""
        if sort_by_column == header:
            indicator = " ↓" if sort_order == "DESC" else " ↑"
        
        return Th(
            header + indicator,
            hx_get=f'/q/{table}',
            hx_vals=json.dumps({"sort_by_column": header, "sort_order": next_order}),
            hx_target="#nav_content",
            style="cursor: pointer;"
        )
    
    # 創建表格行
    table_rows = []
    for i, row in enumerate(rows):
        cells = []
        for header, cell in zip(headers, row):
            if enable_event_links and header == 'event_id' and cell:
                # 為event_id創建連結
                cells.append(Td(A(f"{str(cell)[:8]}...", 
                                 href=f"/event/{cell}", 
                                 hx_get=f"/event/{cell}",
                                 hx_target="#result",
                                 hx_push="true",
                                 style="color: #007bff; text-decoration: underline; cursor: pointer;")))
            else:
                cells.append(Td(str(cell) if cell is not None else ""))
        table_rows.append(Tr(*cells, id=f"row-{page * page_size + i}"))
    
    
    # 如果還有更多數據，添加加載觸發器
    if page + 1 < total_pages:
        load_more_trigger = Tr(
            Td(
                "載入更多...",
                colspan=len(headers),
                style="text-align: center; padding: 20px; color: #666;",
                hx_get=f'/q/{table}',
                hx_vals=json.dumps({
                    "sort_by_column": sort_by_column or "",
                    "sort_order": sort_order,
                    "page": page + 1,
                    "page_size": page_size
                }),
                hx_target="closest tr",
                hx_swap="outerHTML",
                hx_trigger="revealed delay:500ms"
            )
        )
        table_rows.append(load_more_trigger)
    
    if page == 0:
        # 第一頁返回完整表格
        return Table(
            Thead(
                *[create_header(header) for header in headers]
            ),
            Tbody(
                *table_rows,
                id="table-body"
            ),
            id="data-table"
        )
    else:
        # 後續頁面只返回新的行
        return table_rows


@app.post("/upload")
async def upload_breeds(file: UploadFile):
    """Web表單上傳路由，支援三種類型檔案"""
    command = UploadFileCommand(file=file)
    result = await upload_handler.handle(command)
    
    if result["success"]:
        # 根據檔案類型獲取對應資料
        query = GetDataQuery(table_name=result["file_type"])
        data_list, _ = data_query_handler.handle_get_data_query(query)
        table_result = render_table(pd.DataFrame(data_list), table=result["file_type"], page=0)
        
        # 創建詳細的成功訊息
        success_message = Div(
            P(f"✅ {result['message']}", style="color: green; font-weight: bold; margin-bottom: 10px;"),
            Details(
                Summary("詳細資訊"),
                Ul(
                    Li(f"檔案類型: {result['file_type']}"),
                    Li(f"有效記錄: {result['valid_count']} 條"),
                    Li(f"無效記錄: {result['invalid_count']} 條") if result['invalid_count'] > 0 else "",
                    Li(f"重複記錄: {result['duplicates_removed']} 條") if result.get('duplicates_removed', 0) > 0 else "",
                    Li(f"新增記錄: {result.get('inserted_count', 0)} 條") if result.get('inserted_count', 0) > 0 else "",
                    Li(f"刪除記錄: {result.get('deleted_count', 0)} 條") if result.get('deleted_count', 0) > 0 else "",
                    Li(f"保持記錄: {result.get('duplicate_count', 0)} 條") if result.get('duplicate_count', 0) > 0 else "",
                ),
                style="margin-bottom: 15px;"
            )
        )
        
        return Div(
            success_message,
            table_result
        )
    else:
        return Div(
            P(f"❌ 上傳失敗: {result['message']}", style="color: red; font-weight: bold; margin-bottom: 10px;"),
            Details(
                Summary("錯誤詳情"),
                Ul(
                    Li(f"檔案類型: {result.get('file_type', '未知')}"),
                    Li(f"有效記錄: {result.get('valid_count', 0)} 條"),
                    Li(f"無效記錄: {result.get('invalid_count', 0)} 條"),
                )
            ) if result.get('file_type') != 'unknown' else P("請檢查檔案格式和欄位名稱是否正確"),
            style="background-color: #ffe6e6; padding: 15px; border-radius: 5px; margin-bottom: 15px;"
        )

@app.post("/api/upload")
async def api_upload(file: UploadFile):
    """API上傳路由，返回JSON格式，支援三種類型檔案"""
    command = UploadFileCommand(file=file)
    return await upload_handler.handle(command)

nav_tabs = Nav(
    Ul(
        Li(
            Button(
                "Upload",
                {"@click": "tab = 'upload'",
                ":class": "tab === 'upload' ? '' : 'outline'"},
                role="button",
                hx_get="/tab/upload",
                hx_target="#nav_content",
                hx_push="true"
            )
        ),
        Li(
            Button(
                "Events", 
                {"@click": "tab = 'events'",
                ":class": "tab === 'events' ? '' : 'outline'"},
                role="button",
                hx_get="/tab/events",
                hx_target="#nav_content", 
                hx_push="true"
            )
        ),
        Li(
            Button(
                "Breeds",
                {"@click": "tab = 'breeds'",
                ":class": "tab === 'breeds' ? '' : 'outline'"},
                role="button", 
                hx_get="/tab/breeds",
                hx_target="#nav_content",
                hx_push="true"
            )
        ),
        Li(
            Button(
                "Sales",
                {"@click": "tab = 'sales'",
                ":class": "tab === 'sales' ? '' : 'outline'"},
                role="button", 
                hx_get="/tab/sales",
                hx_target="#nav_content",
                hx_push="true"
            )
        ),
        Li(
            Button(
                "Feeds",
                {"@click": "tab = 'feeds'",
                ":class": "tab === 'feeds' ? '' : 'outline'"},
                role="button", 
                hx_get="/tab/feeds",
                hx_target="#nav_content",
                hx_push="true"
            )
        ),
        Li(
            Button(
                "Farm Production",
                {"@click": "tab = 'farm_production'",
                ":class": "tab === 'farm_production' ? '' : 'outline'"},
                role="button", 
                hx_get="/tab/farm_production",
                hx_target="#nav_content",
                hx_push="true"
            )
        ),
        Li(
            Button(
                "SQL",
                {"@click": "tab = 'sql'",
                ":class": "tab === 'sql' ? '' : 'outline'"},
                role="button", 
                hx_get="/tab/sql",
                hx_target="#nav_content",
                hx_push="true"
            )
        )
    ),
    x_data=json.dumps({'tab': 'upload'}),
)

@rt('/')
def index():
    return (Title("Cleansales Upload Helper"),
    Main(nav_tabs, Div(upload_breeds_form, id="nav_content"), Div(id="result"), style="margin: auto; width: 90%;")
    )

@rt('/tab/{tab}')
def tab(tab: str):
    match tab:
        case "upload":
            return upload_breeds_form
        case "events":
            return view_upload_events()
        case "breeds":
            return query_data(table="breed", page=0)
        case "sales":
            return query_data(table="sale", page=0)
        case "feeds":
            return query_data(table="feed", page=0)
        case "farm_production":
            return query_data(table="farm_production", page=0)
        case "sql":
            return sql_query_form
    return upload_breeds_form

@rt('/q/{table}')
def query_data(table: str, sort_by_column: str | None = None, sort_order: str | None = None, page: int = 0, page_size: int = 50, event_id: str | None = None):
    query = GetDataQuery(table_name=table, sort_by_column=sort_by_column, sort_order=sort_order,
                        pagination=PaginationQuery(page=page+1, page_size=page_size), event_id=event_id)
    data, total_pages = data_query_handler.handle_get_data_query(query)
    return render_table(pd.DataFrame(data), table=table, sort_by_column=sort_by_column, sort_order=sort_order or "DESC", page=page, page_size=page_size, total_pages=total_pages)


@rt('/events')
def view_upload_events():
    """查看上傳事件歷史"""
    query = GetUploadEventsQuery(limit=100)
    data = data_query_handler.handle_get_upload_events_query(query)
    
    if not data:
        return Div("目前沒有上傳記錄")
    df = pd.DataFrame(data)
    
    # 格式化顯示
    if 'upload_timestamp' in df.columns:
        df['upload_timestamp'] = pd.to_datetime(df['upload_timestamp']).dt.strftime('%Y-%m-%d %H:%M:%S')
    if 'file_size' in df.columns:
        df['file_size'] = df['file_size'].apply(lambda x: f"{x/1024:.1f} KB" if x else "0 KB")
    if 'processing_time_ms' in df.columns:
        df['processing_time_ms'] = df['processing_time_ms'].apply(lambda x: f"{x} ms" if x else "0 ms")
    
    return Div(
        H2("上傳事件歷史"),
        render_table(df, table="events", sort_by_column="upload_timestamp", sort_order="DESC", page=0, enable_event_links=True),
        style="margin: 20px 0;"
    )

@rt('/event/{event_id}')
def view_event_records(event_id: str):
    """查看特定事件的數據記錄"""
    try:
        # 首先獲取事件信息
        event_query = GetEventDetailsQuery(event_id=event_id)
        event_dict = data_query_handler.handle_get_event_details_query(event_query)
        
        if not event_dict:
            return Div(
                H2("事件記錄"),
                P(f"找不到事件 ID: {event_id}", style="color: red;"),
                A("返回事件列表", href="/events", style="color: #007bff;")
            )
        
        file_type = event_dict['file_type']
        
        # 根據文件類型查詢對應的數據表
        table_map = {
            'breed': 'breed',
            'sale': 'sale', 
            'feed': 'feed',
            'farm_production': 'farm_production'
        }
        
        if file_type not in table_map:
            return Div(
                H2("事件記錄"),
                P(f"不支持的文件類型: {file_type}", style="color: red;"),
                A("返回事件列表", href="/events", style="color: #007bff;")
            )
        
        table_name = table_map[file_type]
        
        # 查詢該事件的所有記錄
        data_query = GetDataQuery(table_name=table_name, event_id=event_id, pagination=PaginationQuery(page=1, page_size=100))
        data_records, total_pages = data_query_handler.handle_get_data_query(data_query)
        
        # 創建返回內容
        content = [
            H2(f"事件記錄: {event_id[:8]}..."),
            Div(
                P(f"文件名: {event_dict['file_name']}", style="margin: 5px 0;"),
                P(f"文件類型: {file_type}", style="margin: 5px 0;"),
                P(f"上傳時間: {event_dict['upload_timestamp']}", style="margin: 5px 0;"),
                P(f"處理狀態: {event_dict['processing_status']}", style="margin: 5px 0;"),
                P(f"新增記錄: {event_dict['inserted_count']} 條", style="margin: 5px 0;"),
                P(f"刪除記錄: {event_dict['deleted_count']} 條", style="margin: 5px 0;"),
                P(f"重複記錄: {event_dict['duplicate_count']} 條", style="margin: 5px 0;"),
                style="background: #f8f9fa; padding: 15px; border-radius: 5px; margin: 15px 0;"
            ),
            # A("返回事件列表", href="/events", style="color: #007bff; margin-bottom: 15px; display: inline-block;")
        ]
        
        if data_records:
            df = pd.DataFrame(data_records)
            
            # 移除event_id欄位以避免重複顯示
            if 'event_id' in df.columns:
                df = df.drop('event_id', axis=1)
            
            content.extend([
                H3(f"數據記錄 ({len(data_records)} 條)"),
                render_table(df, table=file_type, page=0, page_size=100, total_pages=total_pages)
            ])
        else:
            content.append(P("此事件沒有關聯的數據記錄", style="color: #666; font-style: italic;"))
        
        return Div(*content, style="margin: 20px 0;")
        
    except Exception as e:
        return Div(
            H2("事件記錄"),
            P(f"查詢事件記錄失敗: {str(e)}", style="color: red;"),
            A("返回事件列表", href="/events", style="color: #007bff;")
        )

@app.post("/sql")
def execute_sql(sql: str):
    """執行自定義SQL查詢"""
    if not sql.strip():
        return Div("請輸入SQL查詢語句", style="color: red;")
    
    # 基本的SQL安全檢查
    sql_lower = sql.lower().strip()
    if not sql_lower.startswith(('select', 'with')):
        return Div("只允許SELECT和WITH查詢語句", style="color: red;")
    
    # 檢查是否包含危險操作
    dangerous_keywords = ['drop', 'delete', 'update', 'insert', 'alter', 'create', 'truncate']
    if any(keyword in sql_lower for keyword in dangerous_keywords):
        return Div("不允許包含修改數據的SQL語句", style="color: red;")
    
    conn = data_query_handler.get_db_connection()
    try:
        cursor = conn.execute(sql)
        results = cursor.fetchall()
        
        if not results:
            return Div("查詢無結果")
        
        # 將結果轉換為DataFrame
        data = [dict(row) for row in results]
        df = pd.DataFrame(data)
        
        return Div(
            P(f"查詢成功，共 {len(results)} 筆結果"),
            render_table(df, table="sql")
        )
        
    except Exception as e:
        return Div(f"SQL執行錯誤: {str(e)}", style="color: red;")
    finally:
        conn.close()

def main():
    serve()


if __name__ == "__main__":
    main()