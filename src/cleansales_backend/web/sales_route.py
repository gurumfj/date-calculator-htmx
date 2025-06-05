import json

from fasthtml.common import *
from fasthtml.components import H1, Div, Label, P, Script, Style
from postgrest.exceptions import APIError
from starlette.middleware import Middleware
from starlette.middleware.gzip import GZipMiddleware

from cleansales_backend.core.config import get_settings
from cleansales_backend.web.batches_route import _render_exception_component
from cleansales_backend.web.data_service import CachedDataService, DataServiceInterface
from supabase import Client, create_client


def create_data_service() -> DataServiceInterface:
    supabase: Client = create_client(
        supabase_url=get_settings().SUPABASE_CLIENT_URL,
        supabase_key=get_settings().SUPABASE_ANON_KEY,
    )
    return CachedDataService(supabase)


cached_data = create_data_service()
# SVG favicon link
favicon_link = Link(rel="icon", type="image/svg+xml", href="/static/favicon.svg")

tailwind_cdn = Script(src="https://cdn.jsdelivr.net/npm/@tailwindcss/browser@4")

# 自定義樣式 CSS
custom_style = Style("""


""")

app, rt = fast_app(
    live=True,
    key_fname=".sesskey",
    session_cookie="cleansales",
    max_age=3600,
    hdrs=(tailwind_cdn, favicon_link, custom_style),
    pico=False,
    middleware=(Middleware(GZipMiddleware),),
)


# @app.get("/todoist")
# def todoist():
#     try:
#         api = get_todoist_api()
#         projects = api.get_projects()

#         return Div(
#             H1("Todoist", cls="text-2xl font-bold text-gray-800 mb-4"),
#             Label("專案", cls="text-lg font-bold text-gray-800 mb-2", _for="project_id"),
#             Select(
#                 *[Option(p.name, value=p.id) for p in projects],
#                 cls="transition-all duration-300 ease-in-out",
#                 id="project_id",
#                 hx_get="/todoist/q",
#                 hx_target="#task",
#                 hx_trigger="change, load",
#                 hx_indicator="#loading",
#             ),
#             Div(
#                 P("載入中...", cls="text-gray-600"),
#                 cls="flex justify-center items-center h-screen htmx-indicator",
#                 id="loading",
#             ),
#             Div(
#                 id="task",
#             ),
#             cls="container mx-auto px-4 py-3 flex flex-col justify-center items-center",
#         )
#     except Exception as e:
#         return _render_exception_component(e)


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
        return _render_exception_component(e)


@app.get("/")
def sales(offset: int = 0, search: str | None = None):
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
            return Form(
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
                        # hx_push_url="true",
                    ),
                    Span(id="search_error", cls="text-red-500", hx_swap_oob="true"),
                    type="search",
                    cls="flex items-center gap-4 p-2",
                ),
                cls="mb-4",
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
        return _render_exception_component(e)


# @app.get("/todoist/labels")
# def labels():
#     try:
#         api = get_todoist_api()
#         # projects = api.get_projects()
#         # archives_items: list[CompletedItems] = []
#         archives_items = api.get_completed_items(project_id="2352145073")
#         # for project in projects:
#         #     archives_items.append(api.get_completed_items(project_id=project.id))
#         print(archives_items.items[0])
#         labels = [item.labels for item in archives_items.items]
#         return Div(*[Li(l) for l in labels])
#     except Exception as e:
#         return _render_exception_component(e)


# @app.get("/todoist/q")
# def todoist_query(project_id: str | None = None):
#     try:
#         api = get_todoist_api()
#         tasks = api.get_tasks(project_id=project_id)
#         result = []
#         for task in tasks:
#             result.append(
#                 Details(
#                     Summary(
#                         H3(task.content),
#                         Ul(*[Li(l) for l in task.labels]) if task.labels else None,
#                     ),
#                     *[Li(f"{k}: {v}") for k, v in task.to_dict().items()],
#                 )
#             )
#         return Div(*result)
#     except Exception as e:
#         return _render_exception_component(e)
