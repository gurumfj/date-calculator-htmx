import json
import logging
import uuid
from datetime import datetime, timedelta

from fasthtml.common import *
from postgrest.exceptions import APIError
from rich.logging import RichHandler
from starlette.middleware.gzip import GZipMiddleware
from todoist_api_python.api import TodoistAPI

from cleansales_backend.core.config import get_settings
from cleansales_backend.domain.models.batch_aggregate import BatchAggregate
from cleansales_backend.domain.models.feed_record import FeedRecord
from cleansales_backend.domain.models.sale_record import SaleRecord
from cleansales_backend.domain.utils import day_age, week_age
from cleansales_backend.web import CachedDataService, DataServiceInterface
from supabase import Client, create_client

logger = logging.getLogger(__name__)

logging.basicConfig(
    level=logging.INFO,
    handlers=[RichHandler(rich_tracebacks=False, markup=True)],
)


def create_data_service() -> DataServiceInterface:
    supabase: Client = create_client(
        supabase_url=get_settings().SUPABASE_CLIENT_URL,
        supabase_key=get_settings().SUPABASE_ANON_KEY,
    )
    return CachedDataService(supabase)


cached_data = create_data_service()


BTN_PRIMARY = "bg-blue-500 text-white hover:bg-blue-600"
BTN_SECONDARY = "bg-blue-100 text-blue-700 hover:bg-blue-200"

# 添加 TailwindCSS CDN 和自定義樣式
tailwind_cdn = Script(src="https://cdn.jsdelivr.net/npm/@tailwindcss/browser@4")

# 自定義樣式 CSS
custom_style = Style("""
.rotate-180 {
    transform: rotate(180deg);
}


""")

# 初始化 FastAPI 應用
app, rt = fast_app(
    live=True,
    key_fname=".sesskey",
    session_cookie="cleansales",
    max_age=3600,
    hdrs=(tailwind_cdn, custom_style),
    pico=False,
    middleware=(Middleware(GZipMiddleware),),
)


def breeds_selector_component(selected_breed: str, end_date: str) -> FT:
    # 雞種選項列表
    breeds = ["黑羽", "古早", "舍黑", "閹雞"]
    indicator = Div(
        Span("Loading...", cls="text-black opacity-50"),
        id="loading_indicator",
        cls="htmx-indicator",
    )
    # 建立雞種選擇器組件，使用 Tailwind CSS 美化
    return Div(
        Div(
            H3("雞種選擇", cls="text-lg font-semibold mb-2 text-gray-700"),
            Div(
                *[
                    Button(
                        breed,
                        hx_get=f"/batches?breed={breed}&end_date={end_date}",
                        hx_indicator="#loading_indicator",
                        hx_push_url="true",
                        cls=f"px-4 py-2 rounded-md text-sm font-medium {BTN_PRIMARY if breed == selected_breed else BTN_SECONDARY} focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-opacity-50 inline-block mx-1",
                    )
                    for breed in breeds
                ],
                indicator,
                cls="flex flex-row flex-wrap items-center space-x-2",
            ),
            cls="bg-white p-4 rounded-lg shadow-md mb-4",
        ),
        id="breeds_selector",
        hx_swap_oob="true",
        cls="w-full md:w-1/2",
    )


def date_picker_component(end_date_str: str, breed: str) -> FT:
    # 計算前後30天的日期
    earlier_date_str = (datetime.strptime(end_date_str, "%Y-%m-%d") - timedelta(days=30)).strftime("%Y-%m-%d")
    later_date_str = (datetime.strptime(end_date_str, "%Y-%m-%d") + timedelta(days=30)).strftime("%Y-%m-%d")

    # 使用 Tailwind CSS 美化日期選擇器組件
    return Div(
        Form(
            H3("日期範圍選擇", cls="text-lg font-semibold mb-2 text-gray-700"),
            Div(
                # 向前按鈕
                Div(
                    Button(
                        Span("«", cls="text-xl"),
                        hx_get=f"/batches?end_date={earlier_date_str}&breed={breed}",
                        hx_push_url="true",
                        hx_indicator="#loading_indicator",
                        cls="bg-blue-100 hover:bg-blue-200 text-blue-800 font-bold py-2 px-4 rounded-l-lg transition duration-200 ease-in-out w-full",
                    ),
                    cls="w-1/4",
                ),
                # 日期顯示和選擇
                Div(
                    Div(
                        Input(
                            type="date",
                            aria_label="Date",
                            name="end_date",
                            id="end_date",
                            value=end_date_str,
                            hx_get="/batches",
                            hx_trigger="change delay:500ms",
                            hx_indicator="#loading_indicator",
                            cls="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent",
                        ),
                        cls="flex flex-col",
                    ),
                    cls="w-2/4 px-2",
                ),
                # 向後按鈕
                Div(
                    Button(
                        Span("»", cls="text-xl"),
                        hx_get=f"/batches?end_date={later_date_str}&breed={breed}",
                        hx_indicator="#loading_indicator",
                        cls="bg-blue-100 hover:bg-blue-200 text-blue-800 font-bold py-2 px-4 rounded-r-lg transition duration-200 ease-in-out w-full",
                    ),
                    cls="w-1/4",
                ),
                cls="flex items-center mb-2",
            ),
            # 重置按鈕
            Div(
                Button(
                    "重置所有篩選",
                    type="reset",
                    hx_get="/reset",
                    cls="bg-gray-200 hover:bg-gray-300 text-gray-700 font-medium py-1 px-3 rounded-md text-sm transition duration-200 ease-in-out w-full",
                ),
                cls="mt-2",
            ),
            cls="bg-white p-4 rounded-lg shadow-md mb-4",
        ),
        id="date_picker",
        # hx_get="/batches",
        # hx_trigger="change delay:500ms",
        # hx_vals=f'{{"breed": "{breed}"}}',
        # hx_target="#batch_list",
        # hx_indicator="#loading_indicator",
        hx_swap_oob="true",
        cls="w-full md:w-1/2",
    )


@dataclass
class DashboardItem:
    title: str
    value: str


def render_dashboard_component(data: list[DashboardItem]) -> FT:
    """
    Render dashboard component, better for less than 4 digits
    Args:
        data (list[DashboardItem]): Dashboard data
    Returns:
        FT: FastHTML component
    """
    colors = [
        ("bg-red-50", "text-red-600"),
        ("bg-orange-50", "text-orange-600"),
        ("bg-yellow-50", "text-yellow-600"),
        ("bg-green-50", "text-green-600"),
        ("bg-blue-50", "text-blue-600"),
        ("bg-indigo-50", "text-indigo-600"),
        ("bg-purple-50", "text-purple-600"),
        ("bg-violet-50", "text-violet-600"),
    ]

    return Div(  # Grid Frame
        *[
            Div(
                Div(
                    Span(item.value, cls=colors[i % len(colors)][1] + " font-bold text-2xl"),
                    cls="mb-1",
                ),
                P(item.title, cls="text-xs text-gray-500"),
                cls=f"{colors[i % len(colors)][0]} p-3 rounded-lg text-center",
            )
            for i, item in enumerate(data)
        ],
        cls="grid grid-cols-2 md:grid-cols-3 gap-3 mb-4",
    )


def breed_table_component(batch: BatchAggregate) -> FT:
    # 如果沒有品種數據，顯示友好的空狀態提示
    if not batch.breeds:
        return Div(
            P("尚無品種資料", cls="text-gray-500 text-center py-4"),
            cls="bg-gray-50 rounded-lg border border-gray-200 p-2",
        )

    # 使用 Tailwind CSS 美化表格
    return Div(
        Table(
            Thead(
                Tr(
                    Th(
                        "種母場",
                        cls="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider",
                    ),
                    Th(
                        "入雛日",
                        cls="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider",
                    ),
                    Th(
                        "日齡",
                        cls="px-4 py-2 text-center text-xs font-medium text-gray-500 uppercase tracking-wider",
                    ),
                    Th(
                        "週齡",
                        cls="px-4 py-2 text-center text-xs font-medium text-gray-500 uppercase tracking-wider",
                    ),
                    Th(
                        "公數",
                        cls="px-4 py-2 text-right text-xs font-medium text-gray-500 uppercase tracking-wider",
                    ),
                    Th(
                        "母數",
                        cls="px-4 py-2 text-right text-xs font-medium text-gray-500 uppercase tracking-wider",
                    ),
                    cls="bg-gray-50",
                )
            ),
            Tbody(
                *[
                    Tr(
                        Td(
                            breed.supplier or "-",
                            cls="px-4 py-2 whitespace-nowrap text-sm text-gray-700",
                        ),
                        Td(
                            breed.breed_date.strftime("%Y-%m-%d"),
                            cls="px-4 py-2 whitespace-nowrap text-sm text-gray-700",
                        ),
                        Td(
                            day_age(breed.breed_date),
                            cls="px-4 py-2 whitespace-nowrap text-sm text-center text-gray-700",
                        ),
                        Td(
                            week_age(day_age(breed.breed_date)),
                            cls="px-4 py-2 whitespace-nowrap text-sm text-center text-gray-700",
                        ),
                        Td(
                            f"{breed.breed_male:,}",
                            cls="px-4 py-2 whitespace-nowrap text-sm text-right text-gray-700",
                        ),
                        Td(
                            f"{breed.breed_female:,}",
                            cls="px-4 py-2 whitespace-nowrap text-sm text-right text-gray-700",
                        ),
                        cls="hover:bg-gray-50 transition-colors duration-150 ease-in-out"
                        + (" bg-gray-50" if i % 2 == 0 else ""),
                    )
                    for i, breed in enumerate(batch.breeds)
                ]
            ),
            Tfoot(
                Tr(
                    Th(
                        "總和",
                        cls="px-4 py-2 text-left text-xs font-medium text-gray-700",
                    ),
                    Th("", cls="px-4 py-2"),
                    Th("", cls="px-4 py-2"),
                    Th("", cls="px-4 py-2"),
                    Th(
                        f"{sum(breed.breed_male for breed in batch.breeds):,}",
                        cls="px-4 py-2 text-right text-xs font-medium text-gray-700",
                    ),
                    Th(
                        f"{sum(breed.breed_female for breed in batch.breeds):,}",
                        cls="px-4 py-2 text-right text-xs font-medium text-gray-700",
                    ),
                    cls="bg-gray-100 border-t border-gray-200",
                )
            ),
            cls="min-w-full divide-y divide-gray-200",
        ),
        cls="overflow-x-auto rounded-lg shadow-sm border border-gray-200",
    )


def sales_table_component(batch: BatchAggregate) -> FT:
    # 如果沒有銷售數據，顯示友好的空狀態提示
    if not batch.sales:
        return Div(
            P("尚無銷售資料", cls="text-gray-500 text-center py-4"),
            cls="bg-gray-50 rounded-lg border border-gray-200 p-2",
        )
    batch.sales.sort(key=lambda sale: sale.sale_date, reverse=True)

    grouped_sales = groupby(batch.sales, key=lambda sale: sale.sale_date)

    def _sales_records() -> FT:
        thead = Tr(
            Th("客戶", cls="text-left"),
            Th("公數", cls="text-right"),
            Th("母數", cls="text-right"),
            Th("公重", cls="text-right"),
            Th("母重", cls="text-right"),
            Th("公價", cls="text-right"),
            Th("母價", cls="text-right"),
            Th("總重", cls="text-right"),
            Th("單價", cls="text-right"),
            Th("總價", cls="text-right"),
            cls="bg-blue-50 border-b border-gray-200 [&>th]:px-4 [&>th]:py-2 [&>th]:text-blue-900",
        )
        tbody = []
        for i, (sale_date, sales) in enumerate(grouped_sales.items()):
            sales: list[SaleRecord] = list(sales)

            if i % 5 == 0:
                tbody.append(thead)

            tbody.append(
                Tr(
                    Td(
                        sale_date.strftime("%Y-%m-%d"),
                        colspan=10,
                        cls="text-center bg-gray-200 text-gray-500 px-4 py-2 font-bold",
                    )
                ),
            )
            tbody.extend(
                [
                    Tr(
                        Td(sale.customer, cls="text-left"),
                        Td(f"{sale.male_count if sale.male_count else '-'}", cls="text-right"),
                        Td(f"{sale.female_count if sale.female_count else '-'}", cls="text-right"),
                        Td(f"{sale.male_avg_weight:.2f}" if sale.male_avg_weight else "-", cls="text-right"),
                        Td(f"{sale.female_avg_weight:.2f}" if sale.female_avg_weight else "-", cls="text-right"),
                        Td(f"${sale.male_price:.0f}" if sale.male_price else "-", cls="text-right"),
                        Td(f"${sale.female_price:.0f}" if sale.female_price else "-", cls="text-right"),
                        Td(f"{sale.total_weight:.1f}" if sale.total_weight else "-", cls="text-right"),
                        Td(f"${sale.avg_price:.0f}" if sale.avg_price else "-", cls="text-right"),
                        Td(f"${sale.total_price:,.0f}" if sale.total_price else "-", cls="text-right"),
                        cls="[&>td]:px-4 [&>td]:py-2" + (" bg-gray-100" if i % 2 == 1 else ""),
                    )
                    for i, sale in enumerate(sales)
                ]
            )
        return Div(
            Table(
                Tbody(
                    *tbody,
                    cls="whitespace-nowrap text-sm text-gray-700",
                ),
                cls="text-sm font-medium whitespace-nowrap uppercase tracking-wider w-full",
            ),
            cls="overflow-x-auto rounded-lg shadow-sm border border-gray-200",
        )

    # 使用 Tailwind CSS 美化表格
    return Div(
        Div(
            Div(
                # 銷售摘要統計
                Div(
                    Div(
                        Div(
                            H4("銷售摘要", cls="text-base font-medium text-gray-700"),
                            cls="mb-2",
                        ),
                        Div(
                            Div(
                                P("總銷售量", cls="text-xs text-gray-500"),
                                P(
                                    f"{sum(sale.male_count + sale.female_count for sale in batch.sales):,} 隻",
                                    cls="text-lg font-semibold text-gray-800",
                                ),
                                cls="p-3 bg-blue-50 rounded-lg",
                            ),
                            Div(
                                P("總銷售額", cls="text-xs text-gray-500"),
                                P(
                                    f"${sum(int(sale.total_price) for sale in batch.sales if sale.total_price):,}",
                                    cls="text-lg font-semibold text-green-600",
                                ),
                                cls="p-3 bg-green-50 rounded-lg",
                            ),
                            Div(
                                P("平均單價", cls="text-xs text-gray-500"),
                                P(
                                    f"${sum(sale.total_price for sale in batch.sales if sale.total_price) / sum(sale.male_count + sale.female_count for sale in batch.sales):.1f}/隻"
                                    if sum(sale.male_count + sale.female_count for sale in batch.sales) > 0
                                    else "無資料",
                                    cls="text-lg font-semibold text-gray-800",
                                ),
                                cls="p-3 bg-gray-50 rounded-lg",
                            ),
                            cls="grid grid-cols-3 gap-3 mb-4",
                        ),
                        cls="mb-4",
                    ),
                    cls="bg-white p-4 rounded-lg shadow-sm mb-4",
                ),
                _sales_records(),
                # 銷售詳細表格
                cls="overflow-x-auto rounded-lg shadow-sm border border-gray-200",
            ),
            cls="p-4",
        ),
        cls="bg-white rounded-lg border border-gray-200 mb-4 shadow-sm",
    )


def breed_summary(batch: BatchAggregate) -> FT:
    # 如果沒有品種數據，返回空組件
    if not batch.breeds:
        return Div()

    # 創建資訊項目的函數
    def info_item(label: str, value: str | None) -> FT:
        if not value:
            return Div()  # 返回空的 Div 而不是 None，確保返回值始終是 FT 類型
        return Div(
            Span(f"{label}：", cls="text-gray-600 font-medium"),
            Span(value, cls="text-gray-800"),
            cls="mb-2",
        )

    # 使用 Tailwind CSS 美化飼養摘要
    return Div(
        Div(
            H4(
                "飼養資料",
                cls="text-lg font-semibold text-gray-800 mb-3 flex items-center",
            ),
            Div(
                Div(
                    info_item("管理人", batch.breeds[0].farmer_name),
                    info_item("供應商", batch.breeds[0].supplier),
                    info_item("獸醫", batch.breeds[0].veterinarian),
                    cls="md:w-1/2",
                ),
                Div(
                    info_item("農場", batch.breeds[0].farm_name),
                    info_item("地址", batch.breeds[0].address),
                    info_item("許可證號碼", batch.breeds[0].farm_license),
                    cls="md:w-1/2",
                ),
                cls="flex flex-wrap",
            ),
            cls="p-4 bg-white rounded-lg mb-4",
        ),
        name="breed_summary",
    )


def sales_summary(batch: BatchAggregate) -> FT | None:
    # 如果沒有銷售摘要數據，顯示友好的空狀態提示
    if not batch.sales_summary:
        return Div(
            Div(
                Div(
                    Span("💰", cls="text-2xl mr-2"),
                    Span("銷售摘要", cls="text-lg font-medium"),
                    cls="flex items-center mb-2",
                ),
                P("此批次尚無銷售資料", cls="text-gray-500 text-sm"),
                cls="p-4",
            ),
            cls="bg-gray-50 rounded-lg border border-gray-200 mb-4 shadow-sm",
            name="sales_summary",
        )

    # 格式化百分比和數值的輔助函數
    def format_percentage(value):
        if value is None:
            return "-"
        return f"{value * 100:.1f}%"

    def format_weight(value):
        if value is None:
            return "-"
        return f"{value:.2f} 斤"

    def format_price(value):
        if value is None:
            return "-"
        return f"{value:.1f} 元"

    def format_revenue(value):
        if value is None:
            return "-"
        return f"{int(value):,} 元"

    # 銷售摘要卡片
    return Div(
        Div(
            # 標題區域
            Div(
                Div(
                    Span("💰", cls="text-2xl mr-2"),
                    Span("銷售摘要", cls="text-lg font-medium text-gray-800"),
                    cls="flex items-center mb-3",
                ),
                # 主要統計數據卡片
                render_dashboard_component(
                    [
                        DashboardItem(
                            title="銷售成數",
                            value=f"{batch.sales_summary.sales_percentage * 100:.1f}%",
                        ),
                        DashboardItem(
                            title="平均重量",
                            value=f"{batch.sales_summary.avg_weight:.2f} 斤",
                        ),
                        DashboardItem(
                            title="平均單價",
                            value=f"${batch.sales_summary.avg_price_weight:.1f}"
                            if batch.sales_summary.avg_price_weight
                            else "-",
                        ),
                        DashboardItem(
                            title="開場天數",
                            value=f"{batch.sales_summary.sales_duration} 天"
                            if batch.sales_summary.sales_duration
                            else "-",
                        ),
                        DashboardItem(
                            title="開場日齡",
                            value=f"{batch.sales_summary.sales_open_close_dayage[0]} 天"
                            if batch.sales_summary.sales_open_close_dayage
                            else "-",
                        ),
                        DashboardItem(
                            title="結案日齡",
                            value=f"{batch.sales_summary.sales_open_close_dayage[1]} 天"
                            if batch.sales_summary.sales_open_close_dayage
                            else "-",
                        ),
                    ]
                ),
                Div(
                    Table(
                        Thead(
                            Tr(
                                Th(
                                    "",
                                    cls="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider",
                                ),
                                # Th("總體", cls="px-3 py-2 text-center text-xs font-medium text-gray-500 uppercase tracking-wider"),
                                Th(
                                    "公雞",
                                    cls="px-3 py-2 text-center text-xs font-medium text-gray-500 uppercase tracking-wider",
                                ),
                                Th(
                                    "母雞",
                                    cls="px-3 py-2 text-center text-xs font-medium text-gray-500 uppercase tracking-wider",
                                ),
                            )
                        ),
                        Tbody(
                            # 重量行
                            Tr(
                                Td(
                                    "均重",
                                    cls="px-3 py-2 text-sm font-medium text-gray-700",
                                ),
                                # Td(format_weight(batch.sales_summary.avg_weight), cls="px-3 py-2 text-sm text-center text-gray-700"),
                                Td(
                                    format_weight(batch.sales_summary.avg_male_weight),
                                    cls="px-3 py-2 text-sm text-center text-gray-700",
                                ),
                                Td(
                                    format_weight(batch.sales_summary.avg_female_weight),
                                    cls="px-3 py-2 text-sm text-center text-gray-700",
                                ),
                            ),
                            # 單價行
                            Tr(
                                Td(
                                    "均價",
                                    cls="px-3 py-2 text-sm font-medium text-gray-700",
                                ),
                                # Td(format_price(batch.sales_summary.avg_price_weight), cls="px-3 py-2 text-sm text-center text-gray-700"),
                                Td(
                                    format_price(batch.sales_summary.avg_male_price),
                                    cls="px-3 py-2 text-sm text-center text-gray-700",
                                ),
                                Td(
                                    format_price(batch.sales_summary.avg_female_price),
                                    cls="px-3 py-2 text-sm text-center text-gray-700",
                                ),
                            ),
                            # 隻數行
                            Tr(
                                Td(
                                    "銷售",
                                    cls="px-3 py-2 text-sm font-medium text-gray-700",
                                ),
                                Td(
                                    batch.sales_summary.sales_male,
                                    cls="px-3 py-2 text-sm text-center text-gray-700",
                                ),
                                Td(
                                    batch.sales_summary.sales_female,
                                    cls="px-3 py-2 text-sm text-center text-gray-700",
                                ),
                            ),
                            # 剩餘數量
                            Tr(
                                Td(
                                    "剩餘",
                                    cls="px-3 py-2 text-sm font-medium text-gray-700",
                                ),
                                Td(
                                    batch.sales_summary.remaining_male_estimation,
                                    cls="px-3 py-2 text-sm text-center text-gray-700",
                                ),
                                Td(
                                    batch.sales_summary.remaining_female_estimation,
                                    cls="px-3 py-2 text-sm text-center text-gray-700",
                                ),
                            ),
                            cls="[&>tr:nth-child(odd)]:bg-gray-50 [&>tr]:hover:bg-gray-100",
                        ),
                        cls="min-w-full divide-y divide-gray-200",
                    ),
                    cls="overflow-x-auto bg-white rounded-lg border border-gray-200 mb-4",
                ),
                # 日齡信息
                # Div(
                #     Div(
                #         Div(
                #             P("開場最大日齡", cls="text-xs text-gray-500 mb-1"),
                #             P(str(batch.sales_summary.sales_open_close_dayage[0]) if batch.sales_summary.sales_open_close_dayage[0] is not None else "-",
                #               cls="text-sm font-medium text-gray-700"),
                #             cls="flex-1"
                #         ),
                #         Div(
                #             P("結案最小日齡", cls="text-xs text-gray-500 mb-1"),
                #             P(str(batch.sales_summary.sales_open_close_dayage[1]) if batch.sales_summary.sales_open_close_dayage[1] is not None else "-",
                #               cls="text-sm font-medium text-gray-700"),
                #             cls="flex-1"
                #         ),
                #         cls="flex gap-4"
                #     ),
                #     cls="bg-gray-50 p-3 rounded-lg"
                # ),
                cls="p-4",
            ),
            cls="bg-white rounded-lg border border-gray-200 mb-4 shadow-sm",
        ),
        name="sales_summary",
    )


def feed_summary(batch: BatchAggregate) -> FT | None:
    # 如果沒有飼料數據，返回空
    if not batch.feeds:
        return Div(
            Div(
                Div(
                    Span("📊", cls="text-2xl mr-2"),
                    Span("飼料摘要", cls="text-lg font-medium"),
                    cls="flex items-center mb-2",
                ),
                P("此批次尚無飼料資料", cls="text-gray-500 text-sm"),
                cls="p-4",
            ),
            cls="bg-gray-50 rounded-lg border border-gray-200 mb-4 shadow-sm",
            name="feed_summary",
        )

    # 計算飼料統計數據
    feed_manufacturers = set(feed.feed_manufacturer for feed in batch.feeds if feed.feed_manufacturer)
    feed_items = set(feed.feed_item for feed in batch.feeds if feed.feed_item)
    feed_dates = sorted([feed.feed_date for feed in batch.feeds])

    # 如果有日期，計算飼料使用天數
    feed_days = None
    if feed_dates:
        first_date = min(feed_dates)
        last_date = max(feed_dates)
        feed_days = (last_date - first_date).days + 1

    return Div(
        Div(
            # 標題區域
            Div(
                Div(
                    Span("📊", cls="text-2xl mr-2"),
                    Span("飼料摘要", cls="text-lg font-medium text-gray-800"),
                    cls="flex items-center mb-3",
                ),
                # 統計數據卡片
                Div(
                    # 飼料種類
                    Div(
                        Div(
                            Span(len(feed_items), cls="text-2xl font-bold text-blue-600"),
                            cls="mb-1",
                        ),
                        P("飼料種類", cls="text-xs text-gray-500"),
                        cls="bg-blue-50 p-3 rounded-lg text-center",
                    ),
                    # 供應商數量
                    Div(
                        Div(
                            Span(
                                len(feed_manufacturers),
                                cls="text-2xl font-bold text-green-600",
                            ),
                            cls="mb-1",
                        ),
                        P("供應商數量", cls="text-xs text-gray-500"),
                        cls="bg-green-50 p-3 rounded-lg text-center",
                    ),
                    # 飼料記錄數
                    Div(
                        Div(
                            Span(
                                len(batch.feeds),
                                cls="text-2xl font-bold text-purple-600",
                            ),
                            cls="mb-1",
                        ),
                        P("飼料記錄數", cls="text-xs text-gray-500"),
                        cls="bg-purple-50 p-3 rounded-lg text-center",
                    ),
                    # 飼料使用天數
                    Div(
                        Div(
                            Span(
                                feed_days if feed_days is not None else "-",
                                cls="text-2xl font-bold text-amber-600",
                            ),
                            cls="mb-1",
                        ),
                        P("飼料使用天數", cls="text-xs text-gray-500"),
                        cls="bg-amber-50 p-3 rounded-lg text-center",
                    ),
                    cls="grid grid-cols-2 md:grid-cols-4 gap-3",
                ),
                cls="p-4",
            ),
            cls="bg-white rounded-lg border border-gray-200 mb-4 shadow-sm",
        ),
        name="feed_summary",
    )


def feed_table_component(batch: BatchAggregate) -> FT | None:
    # 如果沒有飼料數據，顯示友好的空狀態提示
    if not batch.feeds:
        return Div(
            P("尚無飼料資料", cls="text-gray-500 text-center py-4"),
            cls="bg-gray-50 rounded-lg border border-gray-200 p-2",
        )

    # 按子場位置分組
    sub_location_group = groupby(batch.feeds, key=lambda x: x.sub_location)

    # 渲染單個飼料表格的函數
    def _render_feed_table(feeds: list[FeedRecord]) -> FT:
        # 按日期排序
        feeds.sort(key=lambda x: x.feed_date)

        # 計算飼料統計數據
        feed_manufacturers = set(feed.feed_manufacturer for feed in feeds if feed.feed_manufacturer)
        # feed_items = set(feed.feed_item for feed in feeds if feed.feed_item)

        return Div(
            # 子場位置標題和統計信息
            Div(
                Div(
                    H4(
                        feeds[0].sub_location or "主要場址",
                        cls="text-base font-medium text-gray-800",
                    ),
                    cls="mb-2",
                ),
                Div(
                    Div(
                        P("飼料供應商", cls="text-xs text-gray-500 mb-1"),
                        P(
                            ", ".join(feed_manufacturers) if feed_manufacturers else "無資料",
                            cls="text-sm text-gray-700",
                        ),
                        cls="mr-6",
                    ),
                    # Div(
                    #     P("飼料種類", cls="text-xs text-gray-500 mb-1"),
                    #     P(", ".join(feed_items) if feed_items else "無資料",
                    #       cls="text-sm text-gray-700"),
                    # ),
                    # cls="flex mb-3"
                ),
                cls="bg-white p-3 rounded-t-lg border-b border-gray-200",
            ),
            # 飼料詳細表格
            Div(
                Table(
                    Thead(
                        Tr(
                            Th(
                                "日期",
                                cls="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider",
                            ),
                            Th(
                                "供應商",
                                cls="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider",
                            ),
                            Th(
                                "品項",
                                cls="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider",
                            ),
                            Th(
                                "週齡",
                                cls="px-3 py-2 text-center text-xs font-medium text-gray-500 uppercase tracking-wider",
                            ),
                            Th(
                                "添加劑",
                                cls="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider",
                            ),
                            Th(
                                "備註",
                                cls="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider",
                            ),
                            cls="bg-gray-50",
                        )
                    ),
                    Tbody(
                        *[
                            Tr(
                                Td(
                                    feed.feed_date.strftime("%Y-%m-%d"),
                                    cls="px-3 py-2 whitespace-nowrap text-sm text-gray-700",
                                ),
                                Td(
                                    feed.feed_manufacturer or "-",
                                    cls="px-3 py-2 whitespace-nowrap text-sm text-gray-700",
                                ),
                                Td(
                                    feed.feed_item or "-",
                                    cls="px-3 py-2 whitespace-nowrap text-sm text-gray-700",
                                ),
                                Td(
                                    feed.feed_week or "-",
                                    cls="px-3 py-2 whitespace-nowrap text-sm text-center text-gray-700",
                                ),
                                Td(
                                    feed.feed_additive or "-",
                                    cls="px-3 py-2 text-sm text-gray-700",
                                ),
                                Td(
                                    feed.feed_remark or "-",
                                    cls="px-3 py-2 text-sm text-gray-700",
                                ),
                                cls="hover:bg-gray-50 transition-colors duration-150 ease-in-out"
                                + (" bg-gray-50" if i % 2 == 0 else ""),
                            )
                            for i, feed in enumerate(feeds)
                        ]
                    ),
                    cls="min-w-full divide-y divide-gray-200",
                ),
                cls="overflow-x-auto",
            ),
            cls="mb-6 bg-white rounded-lg shadow-sm overflow-hidden border border-gray-200",
        )

    # 返回所有子場位置的飼料表格
    return Div(
        *[_render_feed_table(list(feeds)) for _, feeds in sub_location_group.items()],
        cls="mt-4",
    )


def production_summary(batch: BatchAggregate) -> FT:
    if not batch.production:
        return Div(
            P("尚無生產資料", cls="text-gray-500 text-center py-4"),
            cls="bg-gray-50 rounded-lg border border-gray-200 p-2",
        )
    data = batch.production[-1]
    # 利潤
    profit = int(data.revenue - data.expenses if data.revenue and data.expenses else 0)
    # 利潤率
    profit_rate = int((profit / data.expenses) * 100) if data.expenses else 0
    return Div(  # 資料聲明
        Div(  # 背景外框
            Div(  # 標題
                Span(  # 標題圖示 report emoji
                    "📜", cls="text-2xl mr-2"
                ),
                Span(  # 標題文字
                    "結場報告", cls="text-lg font-medium text-gray-800"
                ),
                cls="flex items-center mb-3",
            ),
            render_dashboard_component(
                [
                    DashboardItem(
                        title="換肉率",
                        value=f"{data.fcr:.2f}",
                    ),
                    DashboardItem(
                        title="造肉成本",
                        value=f"{data.meat_cost:.2f}元",
                    ),
                    DashboardItem(
                        title="成本單價",
                        value=f"{data.cost_price:.2f}元",
                    ),
                    DashboardItem(
                        title="平均單價",
                        value=f"{data.avg_price:.2f}元",
                    ),
                    DashboardItem(
                        title="利潤",
                        value=f"{profit:,}元",
                    ),
                    DashboardItem(
                        title="利潤率",
                        value=f"{profit_rate:.2f}%",
                    ),
                ]
            ),
            cls="bg-white rounded-lg border border-gray-200 mb-4 shadow-sm p-4",
        ),
        name="production_summary",
    )


def production_table_component(batch: BatchAggregate) -> FT:
    return Div(P("生產資料尚未提供"), cls="text-center")


# 導航標籤組件
def nav_tabs(batch: BatchAggregate, selected_tab: str = "breed") -> FT:
    # 創建標籤按鈕
    tabs = []
    selected_tab_style = "px-4 py-2 text-sm font-medium rounded-t-lg border-b-2 border-blue-500 bg-white text-blue-600 focus:outline-none"
    unselected_tab_style = "px-4 py-2 text-sm font-medium rounded-t-lg border-b-2 border-transparent hover:border-gray-300 bg-gray-100 text-gray-600 hover:text-gray-800 focus:outline-none"

    if batch.breeds:
        tabs.append(
            Div(
                Button(
                    "批次資料",
                    hx_get=f"/content/{batch.batch_name}/breed" if selected_tab != "breed" else None,
                    hx_target=f"#{batch.safe_id}_batch_tab_content",
                    cls=selected_tab_style if selected_tab == "breed" else unselected_tab_style,
                ),
                cls="mr-2",
                disabled=selected_tab == "breed",
            )
        )

    if batch.sales:
        tabs.append(
            Div(
                Button(
                    "銷售記錄",
                    hx_get=f"/content/{batch.batch_name}/sales" if selected_tab != "sales" else None,
                    hx_target=f"#{batch.safe_id}_batch_tab_content",
                    cls=selected_tab_style if selected_tab == "sales" else unselected_tab_style,
                ),
                cls="mr-2",
                disabled=selected_tab == "sales",
            )
        )

    if batch.feeds:
        tabs.append(
            Div(
                Button(
                    "飼料記錄",
                    hx_get=f"/content/{batch.batch_name}/feed" if selected_tab != "feed" else None,
                    hx_target=f"#{batch.safe_id}_batch_tab_content",
                    cls=selected_tab_style if selected_tab == "feed" else unselected_tab_style,
                )
            )
        )

    if batch.production:
        tabs.append(
            Div(
                Button(
                    "結場報告",
                    hx_get=f"/content/{batch.batch_name}/production" if selected_tab != "production" else None,
                    hx_target=f"#{batch.safe_id}_batch_tab_content",
                    cls=selected_tab_style if selected_tab == "production" else unselected_tab_style,
                )
            )
        )

    return Div(
        Div(*tabs, cls="flex border-b border-gray-200"),
        id=f"{batch.safe_id}_batch_nav_tabs",
        hx_swap_oob="true",
        cls="mb-4",
    )


def _sales_progress_component(percentage: float, id: str) -> FT | None:
    # if percentage:
    #     使用 Tailwind CSS 自定義進度條
    percentage = int(percentage * 100)

    # 使用內嵌樣式代替 Tailwind 的動態寬度類
    # 這樣可以精確控制進度條寬度
    return Div(
        Div(
            Div(
                Span(
                    f"{percentage}%",
                    cls="text-xs font-medium text-blue-100 text-center absolute inset-0 flex items-center justify-center",
                )
                if percentage > 10
                else None,
                style=f"width:{percentage}%;",
                cls="bg-gradient-to-r from-blue-600 to-blue-200 h-5 rounded-full relative transition-width duration-600 ease",
                id=f"{id}_progress_bar",
            ),
            cls="w-full bg-gray-200 rounded-full h-5 mb-1 relative overflow-hidden",
        ),
        cls="w-full",
        id=id,
    )


@app.post("/sales_progress")
def sales_progress(percentage: float, id: str):
    return _sales_progress_component(percentage, id)


def batch_list_component(batch_list: dict[str, BatchAggregate]) -> FT:
    # 銷售進度條組件

    # 如果沒有批次數據，顯示空狀態
    if not batch_list:
        return Div(
            Div(
                Div(
                    Div(
                        Span("⚠", cls="text-4xl text-yellow-500 mr-3"),
                        H3(
                            "沒有找到符合條件的批次記錄",
                            cls="text-xl font-medium text-gray-700",
                        ),
                        cls="flex items-center justify-center",
                    ),
                    P(
                        "請嘗試調整篩選條件或選擇不同的雞種。",
                        cls="text-gray-500 mt-2 text-center",
                    ),
                    cls="p-8 bg-gray-50 rounded-lg border border-gray-200",
                ),
                cls="max-w-lg mx-auto",
            ),
            id="batch_list",
            hx_swap_oob="true",
        )

    def week_age_str(batch: BatchAggregate) -> str:
        return ", ".join(
            [week_age(day_age(breed.breed_date)) for breed in sorted(batch.breeds, key=lambda breed: breed.breed_date)]
        )

    # 返回批次列表
    return Div(
        *[
            Details(
                # 批次標題和進度條
                Summary(
                    Div(
                        H3(
                            batch.batch_name,
                            cls="text-lg font-semibold text-gray-800",
                        ),
                        P(
                            f"週齡: {week_age_str(batch)} | {sum([breed.breed_male + breed.breed_female for breed in batch.breeds])}隻",
                            cls="text-sm text-gray-600",
                        ),
                        cls="flex-grow",
                    ),
                    Div(
                        Div(
                            _sales_progress_component(0.0, f"sales_progress_{batch.safe_id}"),
                            hx_post="/sales_progress",
                            # hx_target=f"#sales_progress_{batch.safe_id}",
                            hx_trigger="revealed",
                            hx_swap="outerHTML swap:.6s",
                            hx_vals=f'{{"percentage": {batch.sales_percentage or 0}, "id": "sales_progress_{batch.safe_id}"}}',
                            cls="hidden",
                        ),
                        # P(
                        #     f"銷售進度: {batch.sales_percentage * 100:.0f}%" if batch.sales_percentage else "尚未銷售",
                        #     cls="text-xs text-gray-600",
                        # ),
                        cls="w-1/3",
                    )
                    if batch.sales
                    else None,
                    cls="flex justify-between items-center p-4 cursor-pointer hover:bg-gray-50 open:bg-amber-200",
                    id=f"{batch.safe_id}_batch_summary",
                ),
                # 批次詳細內容
                Div(
                    nav_tabs(batch),
                    Div(
                        breed_summary(batch),
                        breed_table_component(batch),
                        id=f"{batch.safe_id}_batch_tab_content",
                        cls="bg-white p-2 rounded-b-lg",
                    ),
                    Div(
                        P(
                            Span("更新時間: ", cls="text-gray-600"),
                            Span(
                                batch.last_updated_at.strftime("%Y-%m-%d %H:%M:%S"),
                                cls="text-gray-800",
                            ),
                            cls="text-xs",
                        ),
                        P(
                            Span("快取時間: ", cls="text-gray-600"),
                            Span(
                                batch.cached_time.strftime("%Y-%m-%d %H:%M:%S"),
                                cls="text-gray-800",
                            ),
                            cls="text-xs mt-1",
                        ),
                        cls="mt-4 text-right border-t border-gray-100 pt-2 pr-2 pb-2",
                    ),
                    cls="p-2 bg-gray-50 rounded-b-lg border-t border-gray-200",
                ),
                cls="w-full mb-4 bg-white shadow-md overflow-hidden open:bg-amber-50 sm:mb-6 sm:rounded-lg",
                # open="true",
            )
            for batch in sorted(batch_list.values(), key=lambda x: x.breeds[0].breed_date)
        ],
        id="batch_list",
        hx_swap_oob="true",
    )


def _render_exception_component(e: Exception):
    """
    Render exception component
    TODO: reduce excetion presentation on production
    Args:
        e (Exception): Exception to render
    Returns:
        FT: FastHTML component
    """

    def render(title: str):
        # 顯示異常的詳細信息
        error_details = []

        # 解析錯誤訊息，處理可能的嵌套字典
        def parse_error_message(msg):
            # 如果是字典，直接返回
            if isinstance(msg, dict):
                return msg

            # 嘗試解析字串中的字典
            if isinstance(msg, str):
                try:
                    # 處理字典被轉成字串的情況
                    if msg.startswith("{") and msg.endswith("}"):
                        # 使用 eval 小心處理，只在確定是字典的情況下使用
                        import ast

                        return ast.literal_eval(msg)
                except (SyntaxError, ValueError):
                    pass
            return msg

        # 格式化錯誤訊息，處理嵌套結構
        def format_error_dict(error_dict, indent=0):
            if not isinstance(error_dict, dict):
                return str(error_dict)

            result = []
            for k, v in error_dict.items():
                if isinstance(v, dict):
                    result.append(f"{' ' * indent}{k}:")
                    result.append(format_error_dict(v, indent + 2))
                else:
                    result.append(f"{' ' * indent}{k}: {v}")
            return "\n".join(result)

        # 添加異常的主要信息
        error_msg = str(e)
        parsed_error = parse_error_message(error_msg)

        if isinstance(parsed_error, dict):
            formatted_error = format_error_dict(parsed_error)
            error_details.append(
                Li(
                    Pre(
                        formatted_error,
                        cls="bg-gray-100 p-2 rounded text-sm font-mono overflow-x-auto",
                    )
                )
            )
        else:
            error_details.append(Li(P(f"錯誤訊息: {error_msg}", cls="font-semibold text-red-700")))

        # 如果異常有 args 屬性，顯示它
        if hasattr(e, "args") and e.args:
            for i, arg in enumerate(e.args):
                parsed_arg = parse_error_message(arg)
                if isinstance(parsed_arg, dict):
                    formatted_arg = format_error_dict(parsed_arg)
                    error_details.append(Li(H3(f"參數 {i + 1}:", cls="font-semibold mt-2")))
                    error_details.append(
                        Li(
                            Pre(
                                formatted_arg,
                                cls="bg-gray-100 p-2 rounded text-sm font-mono overflow-x-auto",
                            )
                        )
                    )
                else:
                    error_details.append(Li(P(f"參數 {i + 1}: {arg}", cls="text-gray-700")))

        # 如果異常有 __dict__ 屬性，顯示它的內容
        if hasattr(e, "__dict__"):
            for k, v in e.__dict__.items():
                if k != "args" and not k.startswith("_"):
                    parsed_v = parse_error_message(v)
                    if isinstance(parsed_v, dict):
                        formatted_v = format_error_dict(parsed_v)
                        error_details.append(Li(H3(f"{k}:", cls="font-semibold mt-2")))
                        error_details.append(
                            Li(
                                Pre(
                                    formatted_v,
                                    cls="bg-gray-100 p-2 rounded text-sm font-mono overflow-x-auto",
                                )
                            )
                        )
                    else:
                        error_details.append(Li(P(f"{k}: {v}", cls="text-gray-700")))

        # 如果有 __context__，顯示異常的上下文（即引發此異常的原因）
        if e.__context__:
            error_details.append(Li(H3("引發此異常的原因:", cls="mt-4 text-lg font-bold text-red-600")))
            context_msg = str(e.__context__)
            parsed_context = parse_error_message(context_msg)

            if isinstance(parsed_context, dict):
                formatted_context = format_error_dict(parsed_context)
                error_details.append(Li(P(f"{e.__context__.__class__.__name__}:", cls="font-semibold")))
                error_details.append(
                    Li(
                        Pre(
                            formatted_context,
                            cls="bg-gray-100 p-2 rounded text-sm font-mono overflow-x-auto",
                        )
                    )
                )
            else:
                error_details.append(
                    Li(
                        P(
                            f"{e.__context__.__class__.__name__}: {context_msg}",
                            cls="text-gray-700",
                        )
                    )
                )

        # 如果有 traceback，顯示它
        tb_info = []
        tb = e.__traceback__
        while tb:
            tb_info.append(
                f"檔案 '{tb.tb_frame.f_code.co_filename}', 行 {tb.tb_lineno}, 在 {tb.tb_frame.f_code.co_name}"
            )
            tb = tb.tb_next

        if tb_info:
            error_details.append(Li(H3("錯誤追蹤:", cls="mt-4 text-lg font-bold text-red-600")))
            for info in tb_info:
                error_details.append(Li(P(info, cls="text-sm font-mono text-gray-700")))

        return Title(title), Main(
            H1(title, cls="text-3xl font-bold text-red-500 mb-6"),
            Div(
                H2("錯誤詳情:", cls="text-xl font-bold text-red-600 mb-4"),
                Ul(*error_details, cls="space-y-2 mb-6"),
                cls="bg-white p-6 rounded-lg shadow-md",
            ),
            cls="container mx-auto px-4 py-8 bg-gray-50 min-h-screen",
        )

    match e:
        case APIError():
            return render("資料庫查詢錯誤")
        case Exception():
            return render("發生錯誤")


@app.get("/")
def index() -> Any:
    return Redirect("/batches")


@app.get("/batches")
def batches(request: Request, sess: dict, breed: str | None = None, end_date: str | None = None) -> Any:
    try:
        sess["id"] = sess.get("id", uuid.uuid4().hex)
        breed = breed or "黑羽"
        end_date = end_date or datetime.now().strftime("%Y-%m-%d")
        start_date = (datetime.strptime(end_date, "%Y-%m-%d") - timedelta(days=30)).strftime("%Y-%m-%d")
        if request.headers.get("HX-Request"):
            batch_list = cached_data.query_batches(start_date, end_date, breed)
            return (
                breeds_selector_component(breed, end_date),
                date_picker_component(end_date, breed),
                batch_list_component(batch_list),
            )

        batch_list = cached_data.query_batches(start_date, end_date, breed)
        cache_info = cached_data.cache_info()
        hit_rate = (cache_info["hit_count"] / (cache_info["hit_count"] + cache_info["miss_count"])) * 100

        # 使用 Tailwind CSS 美化主頁面佈局
        return (
            Title("雞隻批次查詢系統"),
            Main(
                # 頂部導航欄
                Div(
                    Div(
                        H1("雞隻批次查詢系統", cls="text-3xl font-bold text-white"),
                        cls="container mx-auto px-4 py-3",
                    ),
                    cls="bg-blue-600 shadow-md",
                ),
                # 主要內容區域
                Div(
                    # 篩選器區域 - 使用 flex 佈局
                    Div(
                        Details(
                            Summary(
                                breeds_selector_component(breed, end_date),
                                cls="list-none",
                            ),
                            date_picker_component(end_date, breed),
                            cls="max-h-auto transition-max-height duration-300 ease-in-out open:max-h-500 overflow-hidden",
                        ),
                        cls="container mt-4 px-2 mx-auto sm:px-4",
                    ),
                    # 批次列表區域
                    Div(
                        Div(
                            H2(
                                "批次列表",
                                cls="hidden sm:block text-2xl font-semibold text-gray-800 mb-4",
                            ),
                            batch_list_component(batch_list),
                            cls="bg-white sm:p-6 sm:rounded-lg shadow-md",
                        ),
                        cls="container sm:mx-auto sm:mb-8 sm:px-4",
                    ),
                    cls="bg-gray-100 min-h-screen pb-8",
                ),
                # 頁腳
                Footer(
                    Div(
                        P(
                            f"命中率: {hit_rate:.2f}%",
                            cls="text-sm text-gray-500",
                        ),
                        P(f"Session ID: {sess['id']}", cls="text-sm text-gray-500"),
                        P("© 2025 CleanSales 系統", cls="text-sm text-gray-600 mt-1"),
                        cls="container mx-auto px-4 py-3 text-center",
                    ),
                    cls="bg-gray-200 border-t border-gray-300",
                ),
                # 移除 container 類，因為我們已經在各個區域使用了 container
                cls="flex flex-col min-h-screen",
            ),
        )
    except Exception as e:
        return _render_exception_component(e)


def get_todoist_api() -> TodoistAPI:
    token = get_settings().TODOIST_API_TOKEN
    if not token:
        raise ValueError("請在 .env 檔中設定 TODOIST_API_TOKEN")
    return TodoistAPI(token)


@app.get("/todoist")
def todoist():
    try:
        api = get_todoist_api()
        projects = api.get_projects()

        return Div(
            H1("Todoist", cls="text-2xl font-bold text-gray-800 mb-4"),
            Label("專案", cls="text-lg font-bold text-gray-800 mb-2", _for="project_id"),
            Select(
                *[Option(p.name, value=p.id) for p in projects],
                cls="transition-all duration-300 ease-in-out",
                id="project_id",
                hx_get="/todoist/q",
                hx_target="#task",
                hx_trigger="change, load",
                hx_indicator="#loading",
            ),
            Div(
                P("載入中...", cls="text-gray-600"),
                cls="flex justify-center items-center h-screen htmx-indicator",
                id="loading",
            ),
            Div(
                id="task",
            ),
            cls="container mx-auto px-4 py-3 flex flex-col justify-center items-center",
        )
    except Exception as e:
        return _render_exception_component(e)


@app.get("/sales/q")
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


@app.get("/sales")
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


@app.get("/todoist/labels")
def labels():
    try:
        api = get_todoist_api()
        # projects = api.get_projects()
        # archives_items: list[CompletedItems] = []
        archives_items = api.get_completed_items(project_id="2352145073")
        # for project in projects:
        #     archives_items.append(api.get_completed_items(project_id=project.id))
        print(archives_items.items[0])
        labels = [item.labels for item in archives_items.items]
        return Div(*[Li(l) for l in labels])
    except Exception as e:
        return _render_exception_component(e)


@app.get("/todoist/q")
def todoist_query(project_id: str | None = None):
    try:
        api = get_todoist_api()
        tasks = api.get_tasks(project_id=project_id)
        result = []
        for task in tasks:
            result.append(
                Details(
                    Summary(
                        H3(task.content),
                        Ul(*[Li(l) for l in task.labels]) if task.labels else None,
                    ),
                    *[Li(f"{k}: {v}") for k, v in task.to_dict().items()],
                )
            )
        return Div(*result)
    except Exception as e:
        return _render_exception_component(e)


@app.get("/reset")
def reset(sess: dict) -> Any:
    try:
        sess.clear()
        return Redirect("/batches")
    except Exception as e:
        return str(e)


@app.get("/content/{batch_name}/{tab_type}")
def content(batch_name: str, tab_type: str) -> Any:
    try:
        batch = cached_data.query_batch(batch_name)
        if not batch:
            return str(f"未找到批次 {batch_name}")
        if tab_type == "breed":
            return (
                nav_tabs(batch, "breed"),
                breed_summary(batch),
                breed_table_component(batch),
            )
        if tab_type == "sales":
            return (
                nav_tabs(batch, "sales"),
                sales_summary(batch),
                sales_table_component(batch),
            )
        if tab_type == "feed":
            return (
                nav_tabs(batch, "feed"),
                feed_summary(batch),
                feed_table_component(batch),
            )
        if tab_type == "production":
            return (
                nav_tabs(batch, "production"),
                production_summary(batch),
                production_table_component(batch),
            )
    except Exception as e:
        return str(e)


def main():
    serve()


if __name__ == "__main__":
    main()
