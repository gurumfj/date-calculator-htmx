import hashlib
import json
import logging
from datetime import datetime
from typing import Literal

from fasthtml.common import *
from fasthtml.components import H1, Div, Label, P, Script, Style
from postgrest.exceptions import APIError
from starlette.middleware import Middleware
from starlette.middleware.gzip import GZipMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

from cleansales_backend.core.config import get_settings
from cleansales_backend.web.batches_route import render_error_page
from cleansales_backend.web.data_service import DataServiceInterface, SQLiteDataService

logger = logging.getLogger(__name__)


def create_data_service() -> DataServiceInterface:
    return SQLiteDataService(db_path="./data/sqlite.db")


cached_data = create_data_service()
# SVG favicon link
favicon_link = Link(rel="icon", type="image/svg+xml", href="/static/favicon.svg")

tailwind_cdn = Script(src="https://cdn.jsdelivr.net/npm/@tailwindcss/browser@4")

# 自定義樣式 CSS
custom_style = Style("""


""")

app, rt = fast_app(
    live=get_settings().WEB_LIVE,
    key_fname=".sesskey",
    session_cookie="cleansales",
    max_age=3600,
    hdrs=(tailwind_cdn, favicon_link, custom_style),
    pico=False,
    middleware=(Middleware(GZipMiddleware),),
)


@app.get("/q")
def query_sales(offset: int = 0, search: str | None = None):
    try:
        if search and search.strip() != "":
            result = cached_data.query_sales(search_term=search, offset=offset, page_size=100)
        else:
            result = cached_data.query_sales(offset=offset, page_size=100)
        from starlette.responses import Response

        if not result.data:
            content = Span("未找到結果", id="search_error", cls="text-green-500", hx_swap_oob="true").__html__()
            return Response(content=content, headers={"HX-Reswap": "none"})
        # sales = [SaleRecord.model_validate(data) for data in result.data]
        return [
            Tr(
                # 日期欄位
                Td(
                    sale.sale_date.strftime("%Y-%m-%d"),
                    cls="font-medium text-gray-700",
                ),
                # 批次欄位
                Td(sale.batch_name, cls="text-blue-600 hover:text-blue-800"),
                # 客戶欄位
                Td(sale.customer, cls="text-gray-800"),
                # 公數欄位
                Td(sale.male_count, cls="text-center font-medium"),
                # 母數欄位
                Td(sale.female_count, cls="text-center font-medium"),
                # 公重欄位
                Td(
                    f"{sale.male_avg_weight:.2f}" if sale.male_avg_weight else "-",
                    cls="text-right text-green-700 font-medium",
                ),
                # 母重欄位
                Td(
                    f"{sale.female_avg_weight:.2f}" if sale.female_avg_weight else "-",
                    cls="text-right text-green-700 font-medium",
                ),
                cls="hover:bg-blue-50 transition-colors duration-150 even:bg-gray-50",
            )
            for sale in result.data
        ] + [
            Tr(
                hx_get=f"/sales/q?offset={offset + 100}&search={search}",
                hx_target="#sales_table",
                hx_swap="beforeend",
                hx_trigger="revealed",
            )
        ], Span("", id="search_error", cls="text-red-500", hx_swap_oob="true")
    except APIError:
        # sales_table保持不變，只更新錯誤訊息
        # 返回一個帶有 hx_swap_oob="true" 的 Span，但需要設置額外的 HTTP 頭
        # 告訴 HTMX 不要更新目標元素
        from starlette.responses import Response

        content = Span("錯誤輸入", id="search_error", cls="text-red-500", hx_swap_oob="true").__html__()
        return Response(content=content, headers={"HX-Reswap": "none", "HX-Current-url": "/sales"})
    except Exception as e:
        return render_error_page(e)


@app.get("/")
def sales(req: Request, sess:dict, offset: int = 0, search: str | None = None):
    req.scope['auth'] = sess.get('auth', None)
    try:
        # 頁面佈局組件
        def _layout_component(children: list[FT]):
            return Div(
                # 標題區塊
                Div(
                    H1("銷售紀錄", cls="text-3xl font-bold text-gray-800"),
                    P("所有批次的銷售資料總覽", cls="text-gray-500 mt-1"),
                    cls="mb-6 text-center",
                ),
                # 卡片容器
                Div(*children, cls="bg-white rounded-lg shadow-md p-6 w-full max-w-6xl"),
                cls="container mx-auto px-4 py-8 flex flex-col justify-center items-center",
            )

        # 表頭樣式
        th_style = "px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider"
        # 表格內容樣式
        td_style = "px-6 py-4 whitespace-nowrap text-sm"

        def _form_component():
            return Div(
                Form(
                    Label(
                        "Search",
                        Input(
                            placeholder="Search...",
                            name="search",
                            cls="px-2 py-1 border border-gray-300 rounded",
                            hx_get="/sales/q",
                            hx_target="#sales_table",
                            hx_swap="innerHTML",
                            hx_trigger="change, keyup delay:500ms",
                        ),
                        Span(id="search_error", cls="text-red-500", hx_swap_oob="true"),
                        type="search",
                        cls="flex items-center gap-4 p-2",
                    ),
                    cls="flex-1",
                ),
                A(
                    "API文檔",
                    href="/sales/api/excel-sales",
                    cls="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 transition-colors"
                ),
                cls="mb-4 flex items-center gap-4",
            )

        # 銷售表格組件
        def _sales_table():
            return Div(
                # 表格標題
                Div(H2("銷售明細表", cls="text-xl font-semibold text-gray-700"), cls="mb-4"),
                # 表格容器
                Div(
                    Table(
                        Colgroup(
                            Col(span=1, cls="w-1/8"),  # 日期
                            Col(span=1, cls="w-1/8"),  # 批次
                            Col(span=1, cls="w-1/4"),  # 客戶
                            Col(span=1, cls="w-1/12"),  # 公數
                            Col(span=1, cls="w-1/12"),  # 母數
                            Col(span=1, cls="w-1/8"),  # 公重
                            Col(span=1, cls="w-1/8"),  # 母重
                        ),
                        Thead(
                            Tr(
                                Th("日期"),
                                Th("批次"),
                                Th("客戶"),
                                Th("公數", cls="text-center"),
                                Th("母數", cls="text-center"),
                                Th("公重", cls="text-right"),
                                Th("母重", cls="text-right"),
                                cls=" ".join([f"[&>th]:{s}" for s in th_style.split(" ")]),
                            ),
                            cls="bg-gray-50 border-b border-gray-200",
                        ),
                        Tbody(
                            Tr(
                                hx_get="/sales/q",
                                hx_vals=json.dumps(
                                    {"offset": offset if offset else 0, "search": search if search else ""}
                                ),
                                hx_target="#sales_table",
                                hx_swap="beforeend",
                                hx_trigger="revealed",
                            ),
                            cls=" ".join([f"[&>tr>td]:{s}" for s in td_style.split(" ")]),
                            id="sales_table",
                        ),
                        cls="min-w-full divide-y divide-gray-200 border-collapse",
                    ),
                    cls="overflow-x-auto rounded-md border border-gray-200",
                ),
                cls="w-full",
            )

        return _layout_component([_form_component(), _sales_table()])
    except Exception as e:
        return render_error_page(e)


@app.get("/api/excel-sales")
def get_excel_sales_data(
    request: Request,
    page: int = 1,
    page_size: int = 100,
    batch_name: str | None = None,
    breed_type: Literal["黑羽", "古早", "舍黑", "閹雞"] | None = None,
    batch_status: str | None = None,  # Simplified as string for query params
    start_date: str | None = None,  # Accept as string and parse
    end_date: str | None = None,    # Accept as string and parse
    sort_by: str | None = "sale_date",
    sort_desc: bool = True,
):
    """獲取格式化的銷售數據，適合Excel或Google Apps Script使用
    
    此API提供分頁功能，並以扁平化格式返回銷售數據，
    方便Excel或Google Apps Script進行處理和展示。
    """
    try:
        # Parse dates if provided
        start_date_parsed = None
        end_date_parsed = None
        
        if start_date:
            try:
                start_date_parsed = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
            except ValueError:
                start_date_parsed = datetime.strptime(start_date, "%Y-%m-%d")
                
        if end_date:
            try:
                end_date_parsed = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
            except ValueError:
                end_date_parsed = datetime.strptime(end_date, "%Y-%m-%d")
        
        # Calculate pagination offset
        offset = (page - 1) * page_size
        
        # Get sales data with filters
        search_term = batch_name if batch_name else None
        result = cached_data.query_sales(
            search_term=search_term,
            offset=offset,
            page_size=page_size
        )
        
        # Convert to flattened format for Excel/GAS
        sales_data = []
        for sale in result.data:
            # Filter by breed type if specified
            # Note: This is a simplified filter since we don't have breed info in sale record
            # In a full implementation, you'd need to join with breed data
            
            # Filter by date range
            if start_date_parsed and sale.sale_date < start_date_parsed.date():
                continue
            if end_date_parsed and sale.sale_date > end_date_parsed.date():
                continue
                
            sales_data.append({
                "sale_date": sale.sale_date.strftime("%Y-%m-%d"),
                "batch_name": sale.batch_name,
                "customer": sale.customer,
                "male_count": sale.male_count,
                "female_count": sale.female_count,
                "total_weight": sale.total_weight,
                "total_price": sale.total_price,
                "male_price": sale.male_price,
                "female_price": sale.female_price,
                "avg_price": sale.avg_price,
                "male_avg_weight": sale.male_avg_weight,
                "female_avg_weight": sale.female_avg_weight,
                "unpaid": sale.unpaid,
                "handler": sale.handler,
                "sale_state": sale.sale_state,
                "updated_at": sale.updated_at.isoformat() if sale.updated_at else None,
            })
        
        # Sort data if requested
        if sort_by and sales_data:
            reverse = sort_desc
            if sort_by in sales_data[0]:
                sales_data.sort(key=lambda x: x.get(sort_by, ""), reverse=reverse)
        
        # Calculate pagination info
        total_count = len(sales_data)  # Simplified - in reality would need total count from DB
        total_pages = (total_count + page_size - 1) // page_size
        
        pagination = {
            "page": page,
            "page_size": page_size,
            "total_count": total_count,
            "total_pages": total_pages,
            "has_previous": page > 1,
            "has_next": page < total_pages,
        }
        
        # Prepare metadata
        meta = {
            "generated_at": datetime.now().isoformat(),
            "filters": {
                "batch_name": batch_name,
                "breed_type": breed_type,
                "batch_status": batch_status,
                "start_date": start_date,
                "end_date": end_date,
            },
            "sorting": {
                "sort_by": sort_by,
                "sort_desc": sort_desc,
            },
        }
        
        # Prepare response data
        response_data = {
            "data": sales_data,
            "pagination": pagination,
            "meta": meta,
        }
        
        # Generate ETag
        content_str = json.dumps(response_data)
        content_bytes = content_str.encode("utf-8")
        etag = hashlib.md5(content_bytes).hexdigest()
        
        # Check if content has changed
        if request.headers.get("If-None-Match") == etag:
            return Response(status_code=304, headers={"ETag": etag})
        
        # Return data
        return JSONResponse(
            content=response_data,
            status_code=200,
            headers={"ETag": etag},
        )
        
    except Exception as e:
        logger.error(f"獲取Excel格式銷售數據時發生錯誤: {e}")
        import traceback
        logger.error(traceback.format_exc())
        
        return JSONResponse(
            content={"error": str(e), "type": type(e).__name__},
            status_code=500
        )
