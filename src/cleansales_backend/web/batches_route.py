import json
import logging
import uuid
from datetime import datetime, timedelta
from itertools import groupby
from typing import Annotated

from fasthtml.common import *
from pydantic import BaseModel, StringConstraints, ValidationError, field_validator
from starlette.middleware.gzip import GZipMiddleware

from cleansales_backend.core.config import get_settings
from cleansales_backend.domain.models.batch_aggregate import BatchAggregate
from cleansales_backend.domain.models.feed_record import FeedRecord
from cleansales_backend.domain.models.sale_record import SaleRecord
from cleansales_backend.domain.utils import day_age, week_age
from cleansales_backend.web import CachedDataService, DataServiceInterface
from supabase import Client, create_client

from .resources import common_headers

logger = logging.getLogger(__name__)


def create_data_service() -> DataServiceInterface:
    """建立並返回一個資料服務實例。

    根據環境變數中的 Supabase 配置來初始化 `CachedDataService`。

    Returns:
        DataServiceInterface: 資料服務的實例。
    """
    supabase: Client = create_client(
        supabase_url=get_settings().SUPABASE_CLIENT_URL,
        supabase_key=get_settings().SUPABASE_ANON_KEY,
    )
    return CachedDataService(supabase)


cached_data = create_data_service()


domain_utils_script = Script(src="/static/batches.js")


app, rt = fast_app(
    live=True,
    key_fname=".sesskey",
    session_cookie="cleansales",
    max_age=3600,
    hdrs=(common_headers, domain_utils_script),
    pico=False,
    middleware=(Middleware(GZipMiddleware),),
)


def render_breed_selector(selected_breed: str, end_date: str) -> FT:
    """Renders breed selection component with interactive buttons.

    Args:
        selected_breed: Currently selected breed type
        end_date: Current end date for building breed selection links

    Returns:
        FastHTML component containing breed selection buttons
    """
    available_breeds = ["黑羽", "古早", "舍黑", "閹雞"]
    loading_indicator = Div(
        Span("Loading...", cls="text-black opacity-50"),
        id="loading_indicator",
        cls="htmx-indicator",
    )

    primary_button_style = "bg-blue-500 text-white hover:bg-blue-600"
    secondary_button_style = "bg-blue-100 text-blue-700 hover:bg-blue-200"

    breed_buttons = [
        Button(
            breed,
            hx_get=f"?breed={breed}&end_date={end_date}",
            hx_indicator="#loading_indicator",
            hx_push_url="true",
            cls=f"px-4 py-2 rounded-md text-sm font-medium {primary_button_style if breed == selected_breed else secondary_button_style} focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-opacity-50 inline-block mx-1",
        )
        for breed in available_breeds
    ]

    return Div(
        Div(
            H3("雞種選擇", cls="text-lg font-semibold mb-2 text-gray-700"),
            Div(
                *breed_buttons,
                loading_indicator,
                cls="flex flex-row flex-wrap items-center space-x-2",
            ),
            cls="bg-white p-4 rounded-lg shadow-md mb-4",
        ),
        id="breeds_selector",
        hx_swap_oob="true",
        cls="w-full md:w-1/2",
    )


def render_date_picker(end_date_str: str, breed: str) -> FT:
    """Renders date picker component with navigation controls.

    Args:
        end_date_str: Current selected end date in YYYY-MM-DD format
        breed: Current selected breed for building date change links

    Returns:
        FastHTML component containing date picker functionality
    """
    current_date = datetime.strptime(end_date_str, "%Y-%m-%d")
    previous_month_date = (current_date - timedelta(days=30)).strftime("%Y-%m-%d")
    next_month_date = (current_date + timedelta(days=30)).strftime("%Y-%m-%d")

    navigation_button_style = (
        "bg-blue-100 hover:bg-blue-200 text-blue-800 font-bold py-2 px-4 transition duration-200 ease-in-out w-full"
    )

    return Div(
        Form(
            H3("日期範圍選擇", cls="text-lg font-semibold mb-2 text-gray-700"),
            Div(
                Div(
                    Button(
                        Span("«", cls="text-xl"),
                        hx_get=f"?end_date={previous_month_date}&breed={breed}",
                        hx_push_url="true",
                        hx_indicator="#loading_indicator",
                        cls=f"{navigation_button_style} rounded-l-lg",
                    ),
                    cls="w-1/4",
                ),
                Div(
                    Input(
                        type="date",
                        aria_label="Date",
                        name="end_date",
                        id="end_date",
                        value=end_date_str,
                        hx_get="?",
                        hx_trigger="change delay:500ms",
                        hx_indicator="#loading_indicator",
                        cls="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent",
                    ),
                    cls="w-2/4 px-2",
                ),
                Div(
                    Button(
                        Span("»", cls="text-xl"),
                        hx_get=f"?end_date={next_month_date}&breed={breed}",
                        hx_indicator="#loading_indicator",
                        cls=f"{navigation_button_style} rounded-r-lg",
                    ),
                    cls="w-1/4",
                ),
                cls="flex items-center mb-2",
            ),
            Div(
                Button(
                    "重置所有篩選",
                    type="reset",
                    hx_get="reset",
                    cls="bg-gray-200 hover:bg-gray-300 text-gray-700 font-medium py-1 px-3 rounded-md text-sm transition duration-200 ease-in-out w-full",
                ),
                cls="mt-2",
            ),
            cls="bg-white p-4 rounded-lg shadow-md mb-4",
        ),
        id="date_picker",
        hx_swap_oob="true",
        cls="w-full md:w-1/2",
    )


def render_search_bar():
    return Div(
        Input(
            type="text",
            name="search",
            id="search",
            placeholder="搜尋批次",
            cls="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent",
            hx_get="query",
            hx_trigger="input delay:500ms, compositionend delay:10ms, change",
            hx_target="#search_result",
            hx_indicator="#loading_indicator",
        ),
        cls="w-full md:w-1/2 p-4 bg-white rounded-lg shadow-md mb-4",
    )


def render_search_result(result: list[dict[str, Any]], message: str | None = None) -> FT:
    if message:
        return Div(message, cls="bg-white p-4 rounded-lg shadow-md mb-4")
    if not result:
        return Div("未找到結果", cls="bg-white p-4 rounded-lg shadow-md mb-4")
    return Div(
        Ul(
            *[
                Li(
                    Div(
                        H3(batch.get("batch_name"), cls="font-semibold"),
                        P(
                            Span(batch.get("chicken_breed"), cls="text-sm text-gray-500 mr-2"),
                            Span(batch.get("initial_date"), cls="text-sm text-gray-500 mr-2"),
                            Span(batch.get("final_date"), cls="text-sm text-gray-500 mr-2"),
                            cls="mb-2",
                        ),
                        cls="mb-2",
                        hx_get=f"?breed={batch.get('chicken_breed')}&end_date={batch.get('final_date')}&selected={batch.get('batch_name')}",
                        hx_target="#batch_list",
                        hx_push_url="true",
                        hx_indicator="#loading_indicator",
                    ),
                    {
                        "@click": f'selected = "{batch.get("batch_name")}"',
                        ":class": f'selected === "{batch.get("batch_name")}" ? "bg-amber-50" : "bg-white"',
                    },
                    cls="p-2 rounded-lg shadow-md m-2",
                )
                for batch in result
            ],
            cls="space-y-2 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3",
        ),
        cls="bg-white p-4 rounded-lg shadow-md mb-4",
        x_data=json.dumps({"selected": ""}),
    )


@dataclass
class DashboardMetric:
    title: str
    value: str


def render_dashboard_metrics(metrics: list[DashboardMetric]) -> FT:
    """Renders dashboard component with key metrics.

    Args:
        metrics: List of dashboard metrics to display

    Returns:
        FastHTML component displaying dashboard metrics
    """
    metric_colors = [
        ("bg-red-50", "text-red-600"),
        ("bg-orange-50", "text-orange-600"),
        ("bg-yellow-50", "text-yellow-600"),
        ("bg-green-50", "text-green-600"),
        ("bg-blue-50", "text-blue-600"),
        ("bg-indigo-50", "text-indigo-600"),
        ("bg-purple-50", "text-purple-600"),
        ("bg-violet-50", "text-violet-600"),
    ]

    metric_cards = [
        Div(
            Div(
                Span(metric.value, cls=f"{metric_colors[i % len(metric_colors)][1]} font-bold text-2xl"),
                cls="mb-1",
            ),
            P(metric.title, cls="text-xs text-gray-500"),
            cls=f"{metric_colors[i % len(metric_colors)][0]} p-3 rounded-lg text-center",
        )
        for i, metric in enumerate(metrics)
    ]

    return Div(
        *metric_cards,
        cls="grid grid-cols-2 md:grid-cols-3 gap-3 mb-4",
    )


def render_breed_table(batch: BatchAggregate) -> FT:
    """Renders detailed breed information table for a specific batch.

    Args:
        batch: Batch aggregate containing breed data

    Returns:
        FastHTML component containing breed information table
    """
    if not batch.breeds:
        return Div(
            P("尚無品種資料", cls="text-gray-500 text-center py-4"),
            cls="bg-gray-50 rounded-lg border border-gray-200 p-2",
        )

    table_header_style = "px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider"
    table_cell_style = "px-4 py-2 whitespace-nowrap text-sm text-gray-700"

    return Div(
        Table(
            Thead(
                Tr(
                    Th("種母場", cls=table_header_style),
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
                            cls="px-4 py-2 whitespace-nowrap text-sm text-center text-gray-700",
                            x_text="computeAge(breed_date).dayAgeStr",
                        ),
                        Td(
                            cls="px-4 py-2 whitespace-nowrap text-sm text-center text-gray-700",
                            x_text="computeAge(breed_date).weekAgeStr",
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
                        x_data=json.dumps({"breed_date": breed.breed_date.strftime("%Y-%m-%d")}),
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


def render_sales_table(batch: BatchAggregate) -> FT:
    """呈現特定批次的銷售記錄表格。

    表格包含銷售日期、銷售類型、客戶、隻數、均重、單價、總額和備註等欄位。

    Args:
        batch (BatchAggregate): 包含批次銷售資料的物件。

    Returns:
        FT: 包含銷售記錄表格的 FastHTML 組件。
    """
    # 如果沒有銷售數據，顯示友好的空狀態提示
    if not batch.sales:
        return Div(
            P("尚無銷售資料", cls="text-gray-500 text-center py-4"),
            cls="bg-gray-50 rounded-lg border border-gray-200 p-2",
        )
    batch.sales.sort(key=lambda sale: sale.sale_date, reverse=True)

    grouped_sales = groupby(batch.sales, key=lambda sale: sale.sale_date)

    def _sales_records() -> FT:
        """內部輔助函數，生成銷售記錄表格的內容。"""
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
        for i, (sale_date, records) in enumerate(grouped_sales.items()):
            sales: list[SaleRecord] = list(records)

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


def render_breed_summary(batch: BatchAggregate) -> FT:
    """呈現特定批次的雞種摘要資訊。

    顯示關鍵的雞種相關數據，如雞種名稱、入舍日期、目前週齡等。

    Args:
        batch (BatchAggregate): 包含批次資料的物件。

    Returns:
        FT: 包含雞種摘要資訊的 FastHTML 組件。
    """
    # 如果沒有品種數據，返回空組件
    if not batch.breeds:
        return Div()

    # 創建資訊項目的函數
    def create_info_item(label: str, value: str | None) -> FT:
        if not value:
            return Div()
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
                    create_info_item("管理人", batch.breeds[0].farmer_name),
                    create_info_item("供應商", batch.breeds[0].supplier),
                    create_info_item("獸醫", batch.breeds[0].veterinarian),
                    cls="md:w-1/2",
                ),
                Div(
                    create_info_item("農場", batch.breeds[0].farm_name),
                    create_info_item("地址", batch.breeds[0].address),
                    create_info_item("許可證號碼", batch.breeds[0].farm_license),
                    cls="md:w-1/2",
                ),
                cls="flex flex-wrap",
            ),
            cls="p-4 bg-white rounded-lg mb-4",
        ),
        name="breed_summary",
    )


def render_sales_summary(batch: BatchAggregate) -> FT | None:
    """呈現特定批次的銷售摘要資訊。

    顯示銷售總覽數據，如總銷售隻數、平均售價、總收入等。

    Args:
        batch (BatchAggregate): 包含批次銷售資料的物件。

    Returns:
        FT: 包含銷售摘要資訊的 FastHTML 組件。
    """
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
    def format_percentage(value: float | None) -> str:
        """格式化百分比顯示。"""
        if value is None:
            return "-"
        return f"{value * 100:.1f}%"

    def format_weight(value: float | None) -> str:
        """格式化重量顯示。"""
        if value is None:
            return "-"
        return f"{value:.2f} 斤"

    def format_price(value: float | None) -> str:
        """格式化價格顯示。"""
        if value is None:
            return "-"
        return f"{value:.1f} 元"

    def format_revenue(value: float | None) -> str:
        """格式化總收入顯示。"""
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
                render_dashboard_metrics(
                    [
                        DashboardMetric(
                            title="銷售成數",
                            value=f"{batch.sales_summary.sales_percentage * 100:.1f}%",
                        ),
                        DashboardMetric(
                            title="平均重量",
                            value=f"{batch.sales_summary.avg_weight:.2f} 斤",
                        ),
                        DashboardMetric(
                            title="平均單價",
                            value=f"${batch.sales_summary.avg_price_weight:.1f}"
                            if batch.sales_summary.avg_price_weight
                            else "-",
                        ),
                        DashboardMetric(
                            title="開場天數",
                            value=f"{batch.sales_summary.sales_duration} 天"
                            if batch.sales_summary.sales_duration
                            else "-",
                        ),
                        DashboardMetric(
                            title="開場日齡",
                            value=f"{batch.sales_summary.sales_open_close_dayage[0]} 天"
                            if batch.sales_summary.sales_open_close_dayage
                            else "-",
                        ),
                        DashboardMetric(
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


def render_feed_summary(batch: BatchAggregate) -> FT | None:
    """呈現特定批次的飼料摘要資訊。

    顯示飼料使用總覽，如總耗料量、平均換肉率等。

    Args:
        batch (BatchAggregate): 包含批次飼料資料的物件。

    Returns:
        FT: 包含飼料摘要資訊的 FastHTML 組件。
    """
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


def render_feed_table(batch: BatchAggregate) -> FT | None:
    """呈現特定批次的飼料使用記錄表格。

    表格包含日期、飼料類型、用量、單價、總額和備註等欄位。

    Args:
        batch (BatchAggregate): 包含批次飼料資料的物件。

    Returns:
        FT: 包含飼料記錄表格的 FastHTML 組件。
    """
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
        """內部輔助函數，生成飼料記錄表格的內容。"""
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
                    cls="flex mb-3",
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


def render_production_summary(batch: BatchAggregate) -> FT:
    """呈現特定批次的生產摘要資訊。

    顯示生產效能相關數據，如育成率、總飼料成本、每隻雞成本等。

    Args:
        batch (BatchAggregate): 包含批次生產資料的物件。

    Returns:
        FT: 包含生產摘要資訊的 FastHTML 組件。
    """
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
            render_dashboard_metrics(
                [
                    DashboardMetric(
                        title="換肉率",
                        value=f"{data.fcr:.2f}",
                    ),
                    DashboardMetric(
                        title="造肉成本",
                        value=f"{data.meat_cost:.2f}元",
                    ),
                    DashboardMetric(
                        title="成本單價",
                        value=f"{data.cost_price:.2f}元",
                    ),
                    DashboardMetric(
                        title="平均單價",
                        value=f"{data.avg_price:.2f}元",
                    ),
                    DashboardMetric(
                        title="利潤",
                        value=f"{profit:,}元",
                    ),
                    DashboardMetric(
                        title="利潤率",
                        value=f"{profit_rate:.2f}%",
                    ),
                ]
            ),
            cls="bg-white rounded-lg border border-gray-200 mb-4 shadow-sm p-4",
        ),
        name="production_summary",
    )


def render_production_table(batch: BatchAggregate) -> FT:
    """呈現特定批次的生產記錄表格。

    表格包含生產日期、生產類型、產量、單價、總額和備註等欄位。

    Args:
        batch (BatchAggregate): 包含批次生產資料的物件。

    Returns:
        FT: 包含生產記錄表格的 FastHTML 組件。
    """
    return Div(P("生產資料尚未提供"), cls="text-center")


def render_nav_tabs(batch: BatchAggregate) -> FT:
    """呈現用於在不同批次資訊分頁（如雞種、銷售、飼料、生產）之間導覽的標籤組件。

    Args:
        batch (BatchAggregate): 當前批次的資料物件，主要用於獲取批次名稱以構建連結。

    Returns:
        FT: 包含導覽標籤的 FastHTML 組件。
    """
    tabs_dict = {
        "breed": {
            "key": "breed",
            "title": "批次資料",
            "hx_get": f"content/{batch.batch_name}/breed",
        },
        "sales": {
            "key": "sales",
            "title": "銷售記錄",
            "hx_get": f"content/{batch.batch_name}/sales",
        },
        "feed": {
            "key": "feed",
            "title": "飼料記錄",
            "hx_get": f"content/{batch.batch_name}/feed",
        },
        "production": {
            "key": "production",
            "title": "結場報告",
            "hx_get": f"content/{batch.batch_name}/production",
        },
    }
    tab_list = [
        tabs_dict["breed"],
        tabs_dict["sales"] if batch.sales else None,
        tabs_dict["feed"] if batch.feeds else None,
        tabs_dict["production"] if batch.production else None,
    ]

    def create_tab_button(tab_value: str, tab_title: str, hx_get: str) -> Safe:
        base_button_style = "px-4 py-2 text-sm font-medium rounded-t-lg border-b-2 border-transparent hover:border-gray-300 bg-gray-100 text-gray-600 hover:text-gray-800 focus:outline-none"
        active_button_style = "border-blue-500 bg-white text-blue-600"

        return Button(
            {
                "@click": f"activeTab='{tab_value}'",
                ":disabled": f"activeTab === '{tab_value}'",
                ":class": f"{{'{active_button_style}': activeTab === '{tab_value}'}}",
            },
            tab_title,
            cls=base_button_style,
            hx_get=hx_get,
            hx_target=f"#{batch.safe_id}_batch_tab_content",
        )

    return Div(
        Div(
            *[
                Div(
                    create_tab_button(tab["key"], tab["title"], tab["hx_get"]),
                    cls="mr-2",
                )
                for tab in tab_list
                if tab
            ],
            cls="flex flex-row items-center space-x-2",
            x_data=json.dumps({"activeTab": "breed"}),
        ),
        cls="mb-4",
    )


def render_sales_progress(percentage: float, progress_id: str) -> Safe:
    """呈現一個銷售進度條組件。

    Args:
        percentage (float): 銷售完成的百分比 (0.0 到 100.0)。
        id (str): 組件的 HTML ID。

    Returns:
        Div: 包含進度條的 FastHTML Div 組件。
    """
    if percentage == 0:
        return Safe("")
    percentage = int(percentage * 100)

    raw_html = f"""
    <div id="{progress_id}_progress_bar" class="w-full bg-gray-200 rounded-full h-5 mb-1 relative overflow-hidden">
        <div
        class="bg-gradient-to-r from-blue-600 to-blue-200 h-5 rounded-full relative transition-[width] duration-[2000ms] ease-out" 
        :style="`width: ${{currentValue}}%`"
        x-data="processBar({percentage})"
        x-init="initTransition()">
            <span
                class="text-xs font-medium text-blue-100 text-center absolute inset-0 flex items-center justify-center"
            >
                {percentage}%
            </span>
        </div>
    </div>
    """
    return Safe(raw_html)


def render_batch_list(batch_list: dict[str, BatchAggregate], selected: str | None = None) -> FT:
    """呈現批次列表組件。

    為每個批次顯示一個卡片，包含批次名稱、週齡、銷售進度等摘要資訊，
    並提供導覽標籤以查看詳細資訊。

    Args:
        batch_list (dict[str, BatchAggregate]): 以批次名稱為鍵，批次資料為值的字典。

    Returns:
        FT: 包含批次列表的 FastHTML 組件。
    """
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
        """內部輔助函數，將批次的日齡轉換為週齡和日齡的字串表示。"""
        return ", ".join(
            [week_age(day_age(breed.breed_date)) for breed in sorted(batch.breeds, key=lambda breed: breed.breed_date)]
        )

    alpine_weekage_fn = "${computeAge(breed_date).weekAgeStr}"
    alpine_dayage_fn = "${computeAge(breed_date).dayAgeStr}"
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
                        # P(
                        #     f"週齡: {week_age_str(batch)} | {sum([breed.breed_male + breed.breed_female for breed in batch.breeds])}隻",
                        #     cls="text-sm text-gray-600",
                        # ),
                        Div(
                            Span(
                                "週齡",
                                # cls="text-sm text-gray-600",
                                x_text=f"`週齡: {alpine_weekage_fn} (${alpine_dayage_fn})`",
                                x_data=json.dumps({"breed_date": batch.breeds[0].breed_date.strftime("%Y-%m-%d")}),
                            ),
                            Span(
                                "|",
                                # cls="text-sm text-gray-600",
                            ),
                            Span(
                                f"隻數: {sum([breed.breed_male + breed.breed_female for breed in batch.breeds])}",
                                # cls="text-sm text-gray-600",
                            ),
                            cls="flex items-center gap-2 text-sm text-gray-600",
                        ),
                        cls="flex-grow",
                    ),
                    Div(
                        Div(
                            render_sales_progress(batch.sales_percentage or 0, f"sales_progress_{batch.safe_id}"),
                        ),
                        cls="w-1/3",
                    )
                    if batch.sales
                    else None,
                    cls="flex justify-between items-center p-4 cursor-pointer hover:bg-gray-50 open:bg-amber-200",
                    id=f"{batch.safe_id}_batch_summary",
                ),
                # 批次詳細內容
                Div(
                    render_nav_tabs(batch),
                    Div(
                        render_breed_summary(batch),
                        render_breed_table(batch),
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
                open=True if selected == batch.batch_name else False,
            )
            for batch in sorted(batch_list.values(), key=lambda x: x.breeds[0].breed_date)
        ],
        id="batch_list",
        hx_swap_oob="true",
    )


def render_error_page(exception: Exception) -> Any:
    """Renders standardized error message component.

    Args:
        exception: Exception object to render

    Returns:
        FastHTML component displaying error message
    """
    error_details = []

    def parse_error_message(msg):
        if isinstance(msg, dict):
            return msg

        if isinstance(msg, str):
            try:
                if msg.startswith("{") and msg.endswith("}"):
                    import ast

                    return ast.literal_eval(msg)
            except (SyntaxError, ValueError):
                pass
        return msg

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

    error_msg = str(exception)
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

    if hasattr(exception, "args") and exception.args:
        for i, arg in enumerate(exception.args):
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

    if hasattr(exception, "__dict__"):
        for k, v in exception.__dict__.items():
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

    if exception.__context__:
        error_details.append(Li(H3("引發此異常的原因:", cls="mt-4 text-lg font-bold text-red-600")))
        context_msg = str(exception.__context__)
        parsed_context = parse_error_message(context_msg)

        if isinstance(parsed_context, dict):
            formatted_context = format_error_dict(parsed_context)
            error_details.append(Li(P(f"{exception.__context__.__class__.__name__}:", cls="font-semibold")))
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
                        f"{exception.__context__.__class__.__name__}: {context_msg}",
                        cls="text-gray-700",
                    )
                )
            )

    tb_info = []
    tb = exception.__traceback__
    while tb:
        tb_info.append(f"檔案 '{tb.tb_frame.f_code.co_filename}', 行 {tb.tb_lineno}, 在 {tb.tb_frame.f_code.co_name}")
        tb = tb.tb_next

    if tb_info:
        error_details.append(Li(H3("錯誤追蹤:", cls="mt-4 text-lg font-bold text-red-600")))
        for info in tb_info:
            error_details.append(Li(P(info, cls="text-sm font-mono text-gray-700")))

    return Title("錯誤"), Main(
        H1("錯誤", cls="text-3xl font-bold text-red-500 mb-6"),
        Div(
            H2("錯誤詳情:", cls="text-xl font-bold text-red-600 mb-4"),
            Ul(*error_details, cls="space-y-2 mb-6"),
            cls="bg-white p-6 rounded-lg shadow-md",
        ),
        cls="container mx-auto px-4 py-8 bg-gray-50 min-h-screen",
    )


@app.get("/")
def batch_dashboard_controller(
    request: Request, sess: dict, breed: str | None = None, end_date: str | None = None, selected: str | None = None
) -> Any:
    """Main dashboard controller for batch management system.

    Args:
        request: Starlette Request object
        sess: User session dictionary
        breed: Optional breed filter
        end_date: Optional end date filter in YYYY-MM-DD format

    Returns:
        Complete FastHTML page or error component
    """
    try:
        sess["id"] = sess.get("id", uuid.uuid4().hex)
        breed = breed or "黑羽"
        end_date = end_date or datetime.now().strftime("%Y-%m-%d")
        start_date = (datetime.strptime(end_date, "%Y-%m-%d") - timedelta(days=30)).strftime("%Y-%m-%d")
        if request.headers.get("HX-Request"):
            batch_list = cached_data.query_batches(start_date, end_date, breed)
            return (
                render_breed_selector(breed, end_date),
                render_date_picker(end_date, breed),
                render_batch_list(batch_list, selected),
            )

        batch_list = cached_data.query_batches(start_date, end_date, breed)
        cache_info = cached_data.cache_info()
        hit_rate = (cache_info["hit_count"] / (cache_info["hit_count"] + cache_info["miss_count"])) * 100

        # 使用 Tailwind CSS 美化主頁面佈局
        return (
            Title("批次查詢系統"),
            Main(
                # 頂部導航欄
                Div(
                    Div(
                        H1("批次查詢系統", cls="text-3xl font-bold text-white"),
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
                                render_breed_selector(breed, end_date),
                                cls="list-none",
                            ),
                            render_date_picker(end_date, breed),
                            Details(
                                Summary(
                                    render_search_bar(),
                                    cls="list-none",
                                ),
                                Div(id="search_result"),
                                cls="flex flex-col",
                                open="true",
                            ),
                            cls="max-h-auto transition-max-height duration-300 ease-in-out open:max-h-500 overflow-hidden",
                            open="true",
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
                            render_batch_list(batch_list),
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
        return render_error_page(e)


# 為查詢參數驗證定義 Pydantic 模型
class QueryRouteParams(BaseModel):
    # 搜尋字串，長度在 1 到 10 之間
    search: Annotated[str, StringConstraints(min_length=1, max_length=10)]

    @classmethod
    @field_validator("search")
    def search_must_not_be_blank(cls, value: str) -> str:
        # Pydantic 會確保在調用此驗證器之前 'value' 是一個字串
        # 此驗證器確保搜尋字串在去除前後空白後不為空
        stripped_value = value.strip()
        if not stripped_value:
            raise ValueError("Search term cannot be blank.")
        return stripped_value  # 返回處理過的字串供後續使用


@app.get("/query")
def query_batch_controller(search: str) -> Any:  # fasthtml 將查詢參數 'search' 作為字串傳入
    try:
        try:
            # 使用 Pydantic 模型驗證和處理輸入的 search 參數
            validated_query = QueryRouteParams(search=search)
            # 使用經過驗證且去除前後空白的搜尋詞
            search_term_to_use = validated_query.search
        except ValidationError as e:
            # 若驗證失敗，記錄錯誤訊息
            logger.info(f"Invalid search query provided: '{search}'. Validation errors: {e.errors()}")
            # 返回 Fragment，與原先處理空搜尋的行為一致
            return render_search_result([], "長度需在 1 到 10 之間。")

        result = cached_data.query_batches_by_batch_name(search_term_to_use)
        return render_search_result(result)
    except Exception as e:
        # 捕獲處理或渲染過程中其他未預期的錯誤
        logger.error(f"Error in query_batch_controller for search '{search}': {e}", exc_info=True)
        return render_error_page(e)


@app.get("/reset")
def reset_session_controller(sess: dict) -> Any:
    """Controller for resetting user session and redirecting to main dashboard.

    Args:
        sess: User session dictionary

    Returns:
        Redirect to main page on success, error component on failure
    """
    try:
        sess.clear()
        return Redirect("?")
    except Exception as e:
        logger.error(f"Error resetting session: {e}", exc_info=True)
        return render_error_page(e)


@app.get("/content/{batch_name}/{tab_type}")
def batch_content_controller(batch_name: str, tab_type: str) -> Any:
    """Controller for dynamically loading specific batch content tabs.

    Args:
        batch_name: Name of the batch to query
        tab_type: Type of content tab to display (breed, sales, feed, production)

    Returns:
        Corresponding content tab FastHTML component or error message
    """
    try:
        batch = cached_data.query_batch(batch_name)
        if not batch:
            return Div(P(f"錯誤：未找到批次 {batch_name}"), cls="text-red-500 p-4")

        active_components = []

        if tab_type == "breed":
            active_components.extend(
                [
                    render_breed_summary(batch),
                    render_breed_table(batch),
                ]
            )
        elif tab_type == "sales":
            active_components.extend(
                [
                    render_sales_summary(batch),
                    render_sales_table(batch),
                ]
            )
        elif tab_type == "feed":
            active_components.extend(
                [
                    render_feed_summary(batch),
                    render_feed_table(batch),
                ]
            )
        elif tab_type == "production":
            active_components.extend(
                [
                    render_production_summary(batch),
                    render_production_table(batch),
                ]
            )
        else:
            return Div(P(f"錯誤：無效的分頁類型 '{tab_type}'"), cls="text-red-500 p-4")

        return tuple(active_components) if len(active_components) > 1 else active_components[0]

    except Exception as e:
        logger.error(f"Error loading content for batch {batch_name}, tab {tab_type}: {e}", exc_info=True)
        return render_error_page(e)


def main():
    serve()


if __name__ == "__main__":
    main()
