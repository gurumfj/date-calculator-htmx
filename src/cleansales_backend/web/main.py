import logging
from collections import defaultdict
from datetime import datetime, timedelta
from functools import lru_cache

from fasthtml.common import *
from postgrest.exceptions import APIError
from rich.logging import RichHandler

from cleansales_backend.core.config import get_settings
from cleansales_backend.domain.models.batch_aggregate import BatchAggregate
from cleansales_backend.domain.models.breed_record import BreedRecord
from cleansales_backend.domain.models.feed_record import FeedRecord
from cleansales_backend.domain.models.sale_record import SaleRecord
from cleansales_backend.domain.utils import day_age, week_age
from supabase import Client, create_client

logger = logging.getLogger(__name__)

logging.basicConfig(
    level=logging.INFO,
    handlers=[RichHandler(rich_tracebacks=False, markup=True)],
)
supabase: Client = create_client(
    supabase_url=get_settings().SUPABASE_CLIENT_URL,
    supabase_key=get_settings().SUPABASE_ANON_KEY,
)



class CachedData:
    ALIVE_TIME = 5 * 60 # 5 minutes

    def __init__(self, supabase: Client):
        self.supabase = supabase
        self.batches: dict[str, BatchAggregate] = {}

    def query_batch(self, batch_name: str) -> BatchAggregate | None:
        if batch_name in self.batches:
            cached_batch = self.batches.get(batch_name)
            if cached_batch and cached_batch.cached_time + timedelta(seconds=self.ALIVE_TIME) > datetime.now():
                return cached_batch
        return self.query_single_batch_db(batch_name)

    def query_single_batch_db(self, batch_name: str) -> BatchAggregate | None:
        try:
            batch_response = (self.supabase.table("batchaggregates").select("*")
                .eq("batch_name", batch_name).single()
                .execute())
            if batch_response.data is None:
                return None
            breed_response = (self.supabase.table("breedrecordorm").select("*")
                .eq("batch_name", batch_name)
                .execute())
            sale_response = (self.supabase.table("salerecordorm").select("*")
                .eq("batch_name", batch_name)
                .execute())
            feed_response = (self.supabase.table("feedrecordorm").select("*")
                .eq("batch_name", batch_name)
                .execute())
            breed_records = [BreedRecord.model_validate(data) for data in breed_response.data]
            sale_records = [SaleRecord.model_validate(data) for data in sale_response.data]
            feed_records = [FeedRecord.model_validate(data) for data in feed_response.data]
            batch_aggregate = BatchAggregate(
                breeds=breed_records,
                sales=sale_records,
                feeds=feed_records,
            )
            self.batches[batch_name] = batch_aggregate
            return batch_aggregate
        except APIError as e:
            print(e)
            return None
        except Exception as e:
            print(e)
            return None

    @lru_cache(maxsize=1)
    def query_batches_db(self, start_date: str, end_date: str, chicken_breed: str) -> dict[str, BatchAggregate]:
        try:
            index_response = (self.supabase.table("batchaggregates").select("batch_name")
                .eq("chicken_breed", chicken_breed)
                .gte("final_date", start_date)
                .lte("initial_date", end_date)
                .order("initial_date")
                .execute())
            if index_response.data is None:
                return {}
            batches = [data.get('batch_name') for data in index_response.data]
            breed_response = (self.supabase.table("breedrecordorm").select("*")
                .in_("batch_name", batches)
                .execute())
            sale_response = (self.supabase.table("salerecordorm").select("*")
                .in_("batch_name", batches)
                .execute())
            feed_response = (self.supabase.table("feedrecordorm").select("*")
                .in_("batch_name", batches)
                .execute())
            breed_records = [BreedRecord.model_validate(data) for data in breed_response.data]
            sale_records = [SaleRecord.model_validate(data) for data in sale_response.data]
            feed_records = [FeedRecord.model_validate(data) for data in feed_response.data]
            breed_dict = defaultdict(list)
            sale_dict = defaultdict(list)
            feed_dict = defaultdict(list)
            for breed_record in breed_records:
                breed_dict[breed_record.batch_name].append(breed_record)
            for sale_record in sale_records:
                sale_dict[sale_record.batch_name].append(sale_record)
            for feed_record in feed_records:
                feed_dict[feed_record.batch_name].append(feed_record)
            batchaggr = {}
            for batch_name, breeds in breed_dict.items():
                if batch_name is None:
                    continue
                batch_aggregate = BatchAggregate(
                    breeds=breeds,
                    sales=sale_dict.get(batch_name, []),
                    feeds=feed_dict.get(batch_name, []),
                )
                batchaggr[batch_name] = batch_aggregate
                self.batches[batch_name] = batch_aggregate

            return batchaggr
        except APIError as e:
            print(e)
            return {}
        except Exception as e:
            print(e)
            return {}

cached_data = CachedData(supabase)

BTN_PRIMARY = "bg-blue-500 text-white hover:bg-blue-600"
BTN_SECONDARY = "bg-blue-100 text-blue-700 hover:bg-blue-200"



# 添加 TailwindCSS CDN 到頭部
tailwind_cdn = Link(href="https://cdn.jsdelivr.net/npm/tailwindcss@latest/dist/tailwind.min.css", rel="stylesheet")
app, rt = fast_app(live=True, secret_key="secret", session_cookie="batch_query", max_age=86400, hdrs=(tailwind_cdn,), pico=False)

def breeds_selector_component(selected_breed: str) -> FT:
    # 雞種選項列表
    breeds = ['黑羽', '古早', '舍黑', '閹雞']
    
    # 建立雞種選擇器組件，使用 Tailwind CSS 美化
    return Div(
        Div(
            H3("雞種選擇", cls="text-lg font-semibold mb-2 text-gray-700"),
            Div(
                *[Button(
                    breed,
                    hx_get=f'/query_batches?breed={breed}',
                    cls=f"px-4 py-2 rounded-md text-sm font-medium {BTN_PRIMARY if breed == selected_breed else BTN_SECONDARY} focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-opacity-50 inline-block mx-1"
                ) for breed in breeds],
                cls="flex flex-row flex-wrap items-center space-x-2"
            ),
            cls="bg-white p-4 rounded-lg shadow-md mb-4"
        ),
        id="breeds_selector",
        hx_swap_oob="true",
        cls="w-full md:w-1/2"
    )

def date_picker_component(end_date_str: str)-> FT:
    # 計算前後30天的日期
    earlier_date_str = (datetime.strptime(end_date_str, '%Y-%m-%d') - timedelta(days=30)).strftime('%Y-%m-%d')
    later_date_str = (datetime.strptime(end_date_str, '%Y-%m-%d') + timedelta(days=30)).strftime('%Y-%m-%d')
    
    # 使用 Tailwind CSS 美化日期選擇器組件
    return Div(
        Div(
            H3("日期範圍選擇", cls="text-lg font-semibold mb-2 text-gray-700"),
            Div(
                # 向前按鈕
                Div(
                    Button(
                        Span("«", cls="text-xl"),
                        hx_get=f'/query_batches?end_date={earlier_date_str}',
                        cls="bg-blue-100 hover:bg-blue-200 text-blue-800 font-bold py-2 px-4 rounded-l-lg transition duration-200 ease-in-out w-full"
                    ),
                    cls="w-1/4"
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
                            hx_get='/query_batches',
                            hx_trigger="change",
                            cls="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                        ),
                        cls="flex flex-col"
                    ),
                    cls="w-2/4 px-2"
                ),
                # 向後按鈕
                Div(
                    Button(
                        Span("»", cls="text-xl"),
                        hx_get=f'/query_batches?end_date={later_date_str}',
                        cls="bg-blue-100 hover:bg-blue-200 text-blue-800 font-bold py-2 px-4 rounded-r-lg transition duration-200 ease-in-out w-full"
                    ),
                    cls="w-1/4"
                ),
                cls="flex items-center mb-2"
            ),
            # 重置按鈕
            Div(
                Button(
                    "重置所有篩選",
                    type='reset',
                    hx_get='/reset',
                    cls="bg-gray-200 hover:bg-gray-300 text-gray-700 font-medium py-1 px-3 rounded-md text-sm transition duration-200 ease-in-out w-full"
                ),
                cls="mt-2"
            ),
            cls="bg-white p-4 rounded-lg shadow-md mb-4"
        ),
        id="date_picker",
        hx_swap_oob="true",
        cls="w-full md:w-1/2"
    )

def breed_table_component(batch: BatchAggregate)-> FT:
    # 如果沒有品種數據，顯示友好的空狀態提示
    if not batch.breeds:
        return Div(
            P("尚無品種資料", cls="text-gray-500 text-center py-4"),
            cls="bg-gray-50 rounded-lg border border-gray-200 p-2"
        )
    
    # 使用 Tailwind CSS 美化表格
    return Div(
        Table(
            Thead(
                Tr(
                    Th("種母場", cls="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider"),
                    Th("入雛日", cls="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider"),
                    Th("日齡", cls="px-4 py-2 text-center text-xs font-medium text-gray-500 uppercase tracking-wider"),
                    Th("週齡", cls="px-4 py-2 text-center text-xs font-medium text-gray-500 uppercase tracking-wider"),
                    Th("公數", cls="px-4 py-2 text-right text-xs font-medium text-gray-500 uppercase tracking-wider"),
                    Th("母數", cls="px-4 py-2 text-right text-xs font-medium text-gray-500 uppercase tracking-wider"),
                    cls="bg-gray-50"
                )
            ),
            Tbody(
                *[
                    Tr(
                        Td(breed.supplier or "-", cls="px-4 py-2 whitespace-nowrap text-sm text-gray-700"),
                        Td(breed.breed_date.strftime('%Y-%m-%d'), cls="px-4 py-2 whitespace-nowrap text-sm text-gray-700"),
                        Td(day_age(breed.breed_date), cls="px-4 py-2 whitespace-nowrap text-sm text-center text-gray-700"),
                        Td(week_age(day_age(breed.breed_date)), cls="px-4 py-2 whitespace-nowrap text-sm text-center text-gray-700"),
                        Td(f"{breed.breed_male:,}", cls="px-4 py-2 whitespace-nowrap text-sm text-right text-gray-700"),
                        Td(f"{breed.breed_female:,}", cls="px-4 py-2 whitespace-nowrap text-sm text-right text-gray-700"),
                        cls="hover:bg-gray-50 transition-colors duration-150 ease-in-out" + (" bg-gray-50" if i % 2 == 0 else "")
                    )
                    for i, breed in enumerate(batch.breeds)
                ]
            ),
            Tfoot(
                Tr(
                    Th("總和", cls="px-4 py-2 text-left text-xs font-medium text-gray-700"),
                    Th("", cls="px-4 py-2"),
                    Th("", cls="px-4 py-2"),
                    Th("", cls="px-4 py-2"),
                    Th(f"{sum(breed.breed_male for breed in batch.breeds):,}", cls="px-4 py-2 text-right text-xs font-medium text-gray-700"),
                    Th(f"{sum(breed.breed_female for breed in batch.breeds):,}", cls="px-4 py-2 text-right text-xs font-medium text-gray-700"),
                    cls="bg-gray-100 border-t border-gray-200"
                )
            ),
            cls="min-w-full divide-y divide-gray-200"
        ),
        cls="overflow-x-auto rounded-lg shadow-sm border border-gray-200"
    )


def sales_table_component(batch: BatchAggregate)-> FT:
    # 如果沒有銷售數據，顯示友好的空狀態提示
    if not batch.sales:
        return Div(
            P("尚無銷售資料", cls="text-gray-500 text-center py-4"),
            cls="bg-gray-50 rounded-lg border border-gray-200 p-2"
        )
    
    # 使用 Tailwind CSS 美化表格
    return Div(
        Div(
            # 銷售摘要統計
            Div(
                Div(
                    Div(
                        H4("銷售摘要", cls="text-base font-medium text-gray-700"),
                        cls="mb-2"
                    ),
                    Div(
                        Div(
                            P("總銷售量", cls="text-xs text-gray-500"),
                            P(f"{sum(sale.male_count + sale.female_count for sale in batch.sales):,} 隻", 
                              cls="text-lg font-semibold text-gray-800"),
                            cls="p-3 bg-blue-50 rounded-lg"
                        ),
                        Div(
                            P("總銷售額", cls="text-xs text-gray-500"),
                            P(f"${sum(int(sale.total_price) for sale in batch.sales if sale.total_price):,}", 
                              cls="text-lg font-semibold text-green-600"),
                            cls="p-3 bg-green-50 rounded-lg"
                        ),
                        Div(
                            P("平均單價", cls="text-xs text-gray-500"),
                            P(f"${sum(sale.total_price for sale in batch.sales if sale.total_price) / sum(sale.male_count + sale.female_count for sale in batch.sales):.1f}/隻" 
                              if sum(sale.male_count + sale.female_count for sale in batch.sales) > 0 else "無資料", 
                              cls="text-lg font-semibold text-gray-800"),
                            cls="p-3 bg-gray-50 rounded-lg"
                        ),
                        cls="grid grid-cols-3 gap-3 mb-4"
                    ),
                    cls="mb-4"
                ),
                cls="bg-white p-4 rounded-lg shadow-sm mb-4"
            ),
            
            # 銷售詳細表格
            Table(
                Thead(
                    Tr(
                        Th("日期", cls="px-2 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider"),
                        Th("客戶", cls="px-2 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider"),
                        Th("公數", cls="px-2 py-2 text-right text-xs font-medium text-gray-500 uppercase tracking-wider"),
                        Th("母數", cls="px-2 py-2 text-right text-xs font-medium text-gray-500 uppercase tracking-wider"),
                        Th("公重", cls="px-2 py-2 text-right text-xs font-medium text-gray-500 uppercase tracking-wider"),
                        Th("母重", cls="px-2 py-2 text-right text-xs font-medium text-gray-500 uppercase tracking-wider"),
                        Th("公價", cls="px-2 py-2 text-right text-xs font-medium text-gray-500 uppercase tracking-wider"),
                        Th("母價", cls="px-2 py-2 text-right text-xs font-medium text-gray-500 uppercase tracking-wider"),
                        Th("總重", cls="px-2 py-2 text-right text-xs font-medium text-gray-500 uppercase tracking-wider"),
                        Th("均價", cls="px-2 py-2 text-right text-xs font-medium text-gray-500 uppercase tracking-wider"),
                        Th("總收", cls="px-2 py-2 text-right text-xs font-medium text-gray-500 uppercase tracking-wider"),
                        cls="bg-gray-50"
                    )
                ),
                Tbody(
                    *[
                        Tr(
                            Td(sale.sale_date.strftime('%Y-%m-%d'), cls="px-2 py-2 whitespace-nowrap text-sm text-gray-700"),
                            Td(sale.customer or "-", cls="px-2 py-2 whitespace-nowrap text-sm text-gray-700"),
                            Td(f"{sale.male_count:,}", cls="px-2 py-2 whitespace-nowrap text-sm text-right text-gray-700"),
                            Td(f"{sale.female_count:,}", cls="px-2 py-2 whitespace-nowrap text-sm text-right text-gray-700"),
                            Td(f'{sale.male_avg_weight:.2f}' if sale.male_avg_weight else "-", cls="px-2 py-2 whitespace-nowrap text-sm text-right text-gray-700"),
                            Td(f'{sale.female_avg_weight:.2f}' if sale.female_avg_weight else "-", cls="px-2 py-2 whitespace-nowrap text-sm text-right text-gray-700"),
                            Td(f'${sale.male_price:.1f}' if sale.male_price else "-", cls="px-2 py-2 whitespace-nowrap text-sm text-right text-gray-700"),
                            Td(f'${sale.female_price:.1f}' if sale.female_price else "-", cls="px-2 py-2 whitespace-nowrap text-sm text-right text-gray-700"),
                            Td(f'{sale.total_weight:.1f}' if sale.total_weight else "-", cls="px-2 py-2 whitespace-nowrap text-sm text-right text-gray-700"),
                            Td(f'${sale.avg_price:.1f}' if sale.avg_price else "-", cls="px-2 py-2 whitespace-nowrap text-sm text-right text-gray-700"),
                            Td(f'${int(sale.total_price):,}' if sale.total_price else "-", 
                               cls="px-2 py-2 whitespace-nowrap text-sm text-right font-medium text-green-600"),
                            cls="hover:bg-gray-50 transition-colors duration-150 ease-in-out" + (" bg-gray-50" if i % 2 == 0 else "")
                        )
                        for i, sale in enumerate(sorted(batch.sales, key=lambda sale: sale.sale_date, reverse=True))
                    ]
                ),
                cls="min-w-full divide-y divide-gray-200"
            ),
            cls="overflow-x-auto rounded-lg shadow-sm border border-gray-200"
        ),
        cls="mb-4"
    )
    
    
def breed_summary(batch: BatchAggregate)-> FT:
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
            cls="mb-2"
        )
    
    # 使用 Tailwind CSS 美化飼養摘要
    return Div(
        Div(
            H4("飼養資料", cls="text-lg font-semibold text-gray-800 mb-3 flex items-center"),
            Div(
                Div(
                    info_item("管理人", batch.breeds[0].farmer_name),
                    info_item("供應商", batch.breeds[0].supplier),
                    info_item("獸醫", batch.breeds[0].veterinarian),
                    cls="md:w-1/2"
                ),
                Div(
                    info_item("農場", batch.breeds[0].farm_name),
                    info_item("地址", batch.breeds[0].address),
                    info_item("許可證號碼", batch.breeds[0].farm_license),
                    cls="md:w-1/2"
                ),
                cls="flex flex-wrap"
            ),
            cls="p-4 bg-white rounded-lg mb-4"
        ),
        name="breed_summary"
    )

def sales_summary(batch: BatchAggregate)-> FT | None:
    # 如果沒有銷售摘要數據，顯示友好的空狀態提示
    if not batch.sales_summary:
        return Div(
            Div(
                Div(
                    Span(
                        "💰",
                        cls="text-2xl mr-2"
                    ),
                    Span(
                        "銷售摘要",
                        cls="text-lg font-medium"
                    ),
                    cls="flex items-center mb-2"
                ),
                P(
                    "此批次尚無銷售資料",
                    cls="text-gray-500 text-sm"
                ),
                cls="p-4"
            ),
            cls="bg-gray-50 rounded-lg border border-gray-200 mb-4 shadow-sm",
            name="sales_summary"
        )
    
    # 格式化百分比和數值的輔助函數
    def format_percentage(value):
        if value is None:
            return "-"
        return f"{value*100:.1f}%"
    
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
                    Span(
                        "💰",
                        cls="text-2xl mr-2"
                    ),
                    Span(
                        "銷售摘要",
                        cls="text-lg font-medium text-gray-800"
                    ),
                    cls="flex items-center mb-3"
                ),
                # 主要統計數據卡片
                Div(
                    # 銷售成數
                    Div(
                        Div(
                            Span(
                                format_percentage(batch.sales_summary.sales_percentage),
                                cls="text-2xl font-bold text-blue-600"
                            ),
                            cls="mb-1"
                        ),
                        P(
                            "銷售成數",
                            cls="text-xs text-gray-500"
                        ),
                        cls="bg-blue-50 p-3 rounded-lg text-center"
                    ),
                    # 總銷售數量
                    Div(
                        Div(
                            Span(
                                batch.sales_summary.total_sales or "-",
                                cls="text-2xl font-bold text-green-600"
                            ),
                            cls="mb-1"
                        ),
                        P(
                            "總銷售數量",
                            cls="text-xs text-gray-500"
                        ),
                        cls="bg-green-50 p-3 rounded-lg text-center"
                    ),
                    # 平均重量
                    Div(
                        Div(
                            Span(
                                format_weight(batch.sales_summary.avg_weight),
                                cls="text-2xl font-bold text-purple-600"
                            ),
                            cls="mb-1"
                        ),
                        P(
                            "平均重量",
                            cls="text-xs text-gray-500"
                        ),
                        cls="bg-purple-50 p-3 rounded-lg text-center"
                    ),
                    # 總營收
                    Div(
                        Div(
                            Span(
                                format_revenue(batch.sales_summary.total_revenue),
                                cls="text-2xl font-bold text-amber-600"
                            ),
                            cls="mb-1"
                        ),
                        P(
                            "總營收",
                            cls="text-xs text-gray-500"
                        ),
                        cls="bg-amber-50 p-3 rounded-lg text-center"
                    ),
                    cls="grid grid-cols-2 md:grid-cols-4 gap-3 mb-4"
                ),
                # 詳細數據表格
                Div(
                    Table(
                        Thead(
                            Tr(
                                Th("", cls="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider"),
                                Th("總體", cls="px-3 py-2 text-center text-xs font-medium text-gray-500 uppercase tracking-wider"),
                                Th("公雞", cls="px-3 py-2 text-center text-xs font-medium text-gray-500 uppercase tracking-wider"),
                                Th("母雞", cls="px-3 py-2 text-center text-xs font-medium text-gray-500 uppercase tracking-wider"),
                                cls="bg-gray-50"
                            )
                        ),
                        Tbody(
                            # 重量行
                            Tr(
                                Td("平均重量", cls="px-3 py-2 text-sm font-medium text-gray-700"),
                                Td(format_weight(batch.sales_summary.avg_weight), cls="px-3 py-2 text-sm text-center text-gray-700"),
                                Td(format_weight(batch.sales_summary.avg_male_weight), cls="px-3 py-2 text-sm text-center text-gray-700"),
                                Td(format_weight(batch.sales_summary.avg_female_weight), cls="px-3 py-2 text-sm text-center text-gray-700"),
                                cls="bg-gray-50"
                            ),
                            # 單價行
                            Tr(
                                Td("平均單價", cls="px-3 py-2 text-sm font-medium text-gray-700"),
                                Td(format_price(batch.sales_summary.avg_price_weight), cls="px-3 py-2 text-sm text-center text-gray-700"),
                                Td(format_price(batch.sales_summary.avg_male_price), cls="px-3 py-2 text-sm text-center text-gray-700"),
                                Td(format_price(batch.sales_summary.avg_female_price), cls="px-3 py-2 text-sm text-center text-gray-700")
                            )
                        ),
                        cls="min-w-full divide-y divide-gray-200"
                    ),
                    cls="overflow-x-auto bg-white rounded-lg border border-gray-200 mb-4"
                ),
                # 日齡信息
                Div(
                    Div(
                        Div(
                            P("開場最大日齡", cls="text-xs text-gray-500 mb-1"),
                            P(str(batch.sales_summary.sales_open_close_dayage[0]) if batch.sales_summary.sales_open_close_dayage[0] is not None else "-", 
                              cls="text-sm font-medium text-gray-700"),
                            cls="flex-1"
                        ),
                        Div(
                            P("結案最小日齡", cls="text-xs text-gray-500 mb-1"),
                            P(str(batch.sales_summary.sales_open_close_dayage[1]) if batch.sales_summary.sales_open_close_dayage[1] is not None else "-", 
                              cls="text-sm font-medium text-gray-700"),
                            cls="flex-1"
                        ),
                        cls="flex gap-4"
                    ),
                    cls="bg-gray-50 p-3 rounded-lg"
                ),
                cls="p-4"
            ),
            cls="bg-white rounded-lg border border-gray-200 mb-4 shadow-sm"
        ),
        name="sales_summary"
    )

def feed_summary(batch: BatchAggregate)-> FT | None:
    # 如果沒有飼料數據，返回空
    if not batch.feeds:
        return Div(
            Div(
                Div(
                    Span(
                        "📊",
                        cls="text-2xl mr-2"
                    ),
                    Span(
                        "飼料摘要",
                        cls="text-lg font-medium"
                    ),
                    cls="flex items-center mb-2"
                ),
                P(
                    "此批次尚無飼料資料",
                    cls="text-gray-500 text-sm"
                ),
                cls="p-4"
            ),
            cls="bg-gray-50 rounded-lg border border-gray-200 mb-4 shadow-sm",
            name="feed_summary"
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
                    Span(
                        "📊",
                        cls="text-2xl mr-2"
                    ),
                    Span(
                        "飼料摘要",
                        cls="text-lg font-medium text-gray-800"
                    ),
                    cls="flex items-center mb-3"
                ),
                # 統計數據卡片
                Div(
                    # 飼料種類
                    Div(
                        Div(
                            Span(
                                len(feed_items),
                                cls="text-2xl font-bold text-blue-600"
                            ),
                            cls="mb-1"
                        ),
                        P(
                            "飼料種類",
                            cls="text-xs text-gray-500"
                        ),
                        cls="bg-blue-50 p-3 rounded-lg text-center"
                    ),
                    # 供應商數量
                    Div(
                        Div(
                            Span(
                                len(feed_manufacturers),
                                cls="text-2xl font-bold text-green-600"
                            ),
                            cls="mb-1"
                        ),
                        P(
                            "供應商數量",
                            cls="text-xs text-gray-500"
                        ),
                        cls="bg-green-50 p-3 rounded-lg text-center"
                    ),
                    # 飼料記錄數
                    Div(
                        Div(
                            Span(
                                len(batch.feeds),
                                cls="text-2xl font-bold text-purple-600"
                            ),
                            cls="mb-1"
                        ),
                        P(
                            "飼料記錄數",
                            cls="text-xs text-gray-500"
                        ),
                        cls="bg-purple-50 p-3 rounded-lg text-center"
                    ),
                    # 飼料使用天數
                    Div(
                        Div(
                            Span(
                                feed_days if feed_days is not None else "-",
                                cls="text-2xl font-bold text-amber-600"
                            ),
                            cls="mb-1"
                        ),
                        P(
                            "飼料使用天數",
                            cls="text-xs text-gray-500"
                        ),
                        cls="bg-amber-50 p-3 rounded-lg text-center"
                    ),
                    cls="grid grid-cols-2 md:grid-cols-4 gap-3"
                ),
                cls="p-4"
            ),
            cls="bg-white rounded-lg border border-gray-200 mb-4 shadow-sm"
        ),
        name="feed_summary"
    )

def feed_table_component(batch: BatchAggregate)-> FT | None:
    # 如果沒有飼料數據，顯示友好的空狀態提示
    if not batch.feeds:
        return Div(
            P("尚無飼料資料", cls="text-gray-500 text-center py-4"),
            cls="bg-gray-50 rounded-lg border border-gray-200 p-2"
        )
    
    # 按子場位置分組
    sub_location_group = groupby(batch.feeds, key=lambda x: x.sub_location)
    
    # 渲染單個飼料表格的函數
    def _render_feed_table(feeds: list[FeedRecord])-> FT:
        # 按日期排序
        feeds.sort(key=lambda x: x.feed_date)
        
        # 計算飼料統計數據
        feed_manufacturers = set(feed.feed_manufacturer for feed in feeds if feed.feed_manufacturer)
        # feed_items = set(feed.feed_item for feed in feeds if feed.feed_item)
        
        return Div(
            # 子場位置標題和統計信息
            Div(
                Div(
                    H4(feeds[0].sub_location or "主要場址", 
                       cls="text-base font-medium text-gray-800"),
                    cls="mb-2"
                ),
                Div(
                    Div(
                        P("飼料供應商", cls="text-xs text-gray-500 mb-1"),
                        P(", ".join(feed_manufacturers) if feed_manufacturers else "無資料", 
                          cls="text-sm text-gray-700"),
                        cls="mr-6"
                    ),
                    # Div(
                    #     P("飼料種類", cls="text-xs text-gray-500 mb-1"),
                    #     P(", ".join(feed_items) if feed_items else "無資料", 
                    #       cls="text-sm text-gray-700"),
                    # ),
                    # cls="flex mb-3"
                ),
                cls="bg-white p-3 rounded-t-lg border-b border-gray-200"
            ),
            
            # 飼料詳細表格
            Div(
                Table(
                    Thead(
                        Tr(
                            Th("日期", cls="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider"),
                            Th("供應商", cls="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider"),
                            Th("品項", cls="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider"),
                            Th("週齡", cls="px-3 py-2 text-center text-xs font-medium text-gray-500 uppercase tracking-wider"),
                            Th("添加劑", cls="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider"),
                            Th("備註", cls="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider"),
                            cls="bg-gray-50"
                        )
                    ),
                    Tbody(
                        *[
                            Tr(
                                Td(feed.feed_date.strftime('%Y-%m-%d'), cls="px-3 py-2 whitespace-nowrap text-sm text-gray-700"),
                                Td(feed.feed_manufacturer or "-", cls="px-3 py-2 whitespace-nowrap text-sm text-gray-700"),
                                Td(feed.feed_item or "-", cls="px-3 py-2 whitespace-nowrap text-sm text-gray-700"),
                                Td(feed.feed_week or "-", cls="px-3 py-2 whitespace-nowrap text-sm text-center text-gray-700"),
                                Td(feed.feed_additive or "-", cls="px-3 py-2 text-sm text-gray-700"),
                                Td(feed.feed_remark or "-", cls="px-3 py-2 text-sm text-gray-700"),
                                cls="hover:bg-gray-50 transition-colors duration-150 ease-in-out" + (" bg-gray-50" if i % 2 == 0 else "")
                            )
                            for i, feed in enumerate(feeds)
                        ]
                    ),
                    cls="min-w-full divide-y divide-gray-200"
                ),
                cls="overflow-x-auto"
            ),
            cls="mb-6 bg-white rounded-lg shadow-sm overflow-hidden border border-gray-200"
        )
    
    # 返回所有子場位置的飼料表格
    return Div(
        *[_render_feed_table(list(feeds)) for _, feeds in sub_location_group.items()],
        cls="mt-4"
    )
    

# 導航標籤組件
def nav_tabs(batch: BatchAggregate, selected_tab: str="breed")-> FT:
    # 創建標籤按鈕
    tabs = []
    selected_tab_style = "px-4 py-2 text-sm font-medium rounded-t-lg border-b-2 border-blue-500 bg-white text-blue-600 focus:outline-none"
    unselected_tab_style = "px-4 py-2 text-sm font-medium rounded-t-lg border-b-2 border-transparent hover:border-gray-300 bg-gray-100 text-gray-600 hover:text-gray-800 focus:outline-none"
    
    if batch.breeds:
        tabs.append(
            Div(
                Button(
                    "批次資料",
                    hx_get=f'/content/{batch.batch_name}/breed',
                    hx_target=f"#{batch.safe_id}_batch_tab_content",
                    cls=selected_tab_style if selected_tab == "breed" else unselected_tab_style
                ),
                cls="mr-2"
            )
        )
        
    if batch.sales:
        tabs.append(
            Div(
                Button(
                    "銷售記錄",
                    hx_get=f'/content/{batch.batch_name}/sales',
                    hx_target=f"#{batch.safe_id}_batch_tab_content",
                    cls=selected_tab_style if selected_tab == "sales" else unselected_tab_style
                ),
                cls="mr-2"
            )
        )
        
    if batch.feeds:
        tabs.append(
            Div(
                Button(
                    "飼料記錄",
                    hx_get=f'/content/{batch.batch_name}/feed',
                    hx_target=f"#{batch.safe_id}_batch_tab_content",
                    cls=selected_tab_style if selected_tab == "feed" else unselected_tab_style
                )
            )
        )
        
    return Div(
        Div(
            *tabs,
            cls="flex border-b border-gray-200"
        ),
        id=f"{batch.safe_id}_batch_nav_tabs",
        hx_swap_oob="true",
        cls="mb-4"
    )

def batch_list_component(batch_list: dict[str, BatchAggregate])-> FT:
    # 銷售進度條組件
    def _sales_progress_component(batch: BatchAggregate)-> FT | None:
        if batch.sales_percentage:
            # 使用 Tailwind CSS 自定義進度條
            percentage = int(batch.sales_percentage * 100)
            
            # 使用內嵌樣式代替 Tailwind 的動態寬度類
            # 這樣可以精確控制進度條寬度
            return Div(
                Div(
                    Div(
                        Div(
                            f"{percentage}%",
                            cls="text-xs font-medium text-blue-100 text-center absolute inset-0 flex items-center justify-center"
                        ),
                        style=f"width: {percentage}%",
                        cls="bg-blue-600 h-5 rounded-full relative"
                    ),
                    cls="w-full bg-gray-200 rounded-full h-5 mb-1 relative"
                ),
                cls="w-full"
            )
        return None

    # 如果沒有批次數據，顯示空狀態
    if not batch_list:
        return Div(
            Div(
                Div(
                    Div(
                        Span("⚠", cls="text-4xl text-yellow-500 mr-3"),
                        H3("沒有找到符合條件的批次記錄", cls="text-xl font-medium text-gray-700"),
                        cls="flex items-center justify-center"
                    ),
                    P("請嘗試調整篩選條件或選擇不同的雞種。", cls="text-gray-500 mt-2 text-center"),
                    cls="p-8 bg-gray-50 rounded-lg border border-gray-200"
                ),
                cls="max-w-lg mx-auto"
            ),
            id="batch_list", 
            hx_swap_oob="true"
        )

    weekages_str = lambda batch: ', '.join([week_age(day_age(breed.breed_date)) for breed in sorted(batch.breeds, key=lambda breed: breed.breed_date)])

    # 返回批次列表
    return Div(
        *[
            Div(
                # 批次標題和進度條
                Div(
                    Div(
                        H3(batch.batch_name, cls="text-lg font-semibold text-gray-800"),
                        P(f"週齡: {weekages_str(batch)} | {sum([breed.breed_male + breed.breed_female for breed in batch.breeds])}隻",
                          cls="text-sm text-gray-600"),
                        cls="flex-grow"
                    ),
                    Div(
                        _sales_progress_component(batch) if batch.sales_percentage else None,
                        P(f"銷售進度: {int(batch.sales_percentage * 100)}%" if batch.sales_percentage else "尚未銷售", 
                          cls="text-xs text-gray-600"),
                        cls="w-1/3"
                    ) if batch.sales else None,
                    cls="flex justify-between items-center p-4 cursor-pointer hover:bg-gray-50 transition-colors duration-200",
                    onclick=f"this.nextElementSibling.classList.toggle('hidden'); this.querySelector('.toggle-icon').classList.toggle('rotate-180');"
                ),
                
                # 批次詳細內容
                Div(
                    nav_tabs(batch),
                    Div(
                        breed_summary(batch),
                        breed_table_component(batch),
                        id=f"{batch.safe_id}_batch_tab_content",
                        cls="bg-white p-4 rounded-b-lg"
                    ),
                    Div(
                        P(
                            Span("更新時間: ", cls="text-gray-600"),
                            Span(batch.last_updated_at.strftime('%Y-%m-%d %H:%M:%S'), cls="text-gray-800"),
                            cls="text-xs"
                        ),
                        P(
                            Span("快取時間: ", cls="text-gray-600"),
                            Span(batch.cached_time.strftime('%Y-%m-%d %H:%M:%S'), cls="text-gray-800"),
                            cls="text-xs mt-1"
                        ),
                        cls="mt-4 text-right border-t border-gray-100 pt-2"
                    ),
                    cls="hidden p-4 bg-gray-50 rounded-b-lg border-t border-gray-200"
                ),
                cls="mb-4 bg-white rounded-lg shadow-md overflow-hidden"
            )
            for batch in sorted(batch_list.values(), key=lambda x: x.breeds[0].breed_date)
        ], 
        id="batch_list", 
        hx_swap_oob="true"
    )

@app.get("/")
def index()-> Any:
    return Redirect("/batches")

@app.get("/batches")
def batches(sess:dict)-> Any:
    try:
        breed = sess.get("breed", "黑羽")
        end_date_str = sess.get("end_date", datetime.now().strftime('%Y-%m-%d'))
        start_date_str = (datetime.strptime(end_date_str, '%Y-%m-%d') - timedelta(days=30)).strftime('%Y-%m-%d')
        batch_list = cached_data.query_batches_db(start_date_str, end_date_str, breed)
        
        # 使用 Tailwind CSS 美化主頁面佈局
        return Main(
            # 頂部導航欄
            Div(
                Div(
                    H1("雞隻批次查詢系統", cls="text-3xl font-bold text-white"),
                    cls="container mx-auto px-4 py-3"
                ),
                cls="bg-blue-600 shadow-md mb-6"
            ),
            
            # 主要內容區域
            Div(
                # 篩選器區域 - 使用 flex 佈局
                Div(
                    Div(
                        breeds_selector_component(breed),
                        date_picker_component(end_date_str),
                        cls="flex flex-col md:flex-row space-y-4 md:space-y-0 md:space-x-4 mb-6"
                    ),
                    cls="container mx-auto px-4"
                ),
                
                # 批次列表區域
                Div(
                    Div(
                        H2("批次列表", cls="text-2xl font-semibold text-gray-800 mb-4"),
                        batch_list_component(batch_list),
                        cls="bg-white p-6 rounded-lg shadow-md"
                    ),
                    cls="container mx-auto px-4 mb-8"
                ),
                
                cls="bg-gray-100 min-h-screen pb-8"
            ),
            
            # 頁腳
            Footer(
                Div(
                    P(f"查詢快取資訊: {cached_data.query_batches_db.cache_info()}", 
                      cls="text-sm text-gray-500"),
                    P("© 2025 CleanSales 系統", cls="text-sm text-gray-600 mt-1"),
                    cls="container mx-auto px-4 py-3 text-center"
                ),
                cls="bg-gray-200 border-t border-gray-300"
            ),
            
            # 移除 container 類，因為我們已經在各個區域使用了 container
            cls="flex flex-col min-h-screen"
        )
    except APIError as e:
        return Main(
            Div(
                Div(
                    Div(
                        H1("資料庫查詢錯誤", cls="text-2xl font-bold text-red-600 mb-4"),
                        P(str(e), cls="text-gray-700"),
                        cls="bg-white p-8 rounded-lg shadow-md max-w-2xl mx-auto"
                    ),
                    cls="container mx-auto px-4 py-12"
                ),
                cls="bg-gray-100 min-h-screen"
            )
        )
    except Exception as e:
        return Main(
            Div(
                Div(
                    Div(
                        H1("發生錯誤", cls="text-2xl font-bold text-red-600 mb-4"),
                        P(str(e), cls="text-gray-700"),
                        cls="bg-white p-8 rounded-lg shadow-md max-w-2xl mx-auto"
                    ),
                    cls="container mx-auto px-4 py-12"
                ),
                cls="bg-gray-100 min-h-screen"
            )
        )

@app.get("/query_batches")
def query_batches(sess:dict, breed: str|None=None, end_date: str|None=None)-> Any:
    try:
        if breed:
            sess["breed"] = breed
            end_date_str = sess.get("end_date", datetime.now().strftime('%Y-%m-%d'))
            start_date_str = (datetime.strptime(end_date_str, '%Y-%m-%d') - timedelta(days=30)).strftime('%Y-%m-%d')
            batch_list = cached_data.query_batches_db(start_date_str, end_date_str, breed)
            return breeds_selector_component(breed), batch_list_component(batch_list)
        if end_date:
            sess["end_date"] = end_date
            end_date_str = sess.get("end_date", datetime.now().strftime('%Y-%m-%d'))
            start_date_str = (datetime.strptime(end_date_str, '%Y-%m-%d') - timedelta(days=30)).strftime('%Y-%m-%d')
            batch_list = cached_data.query_batches_db(start_date_str, end_date_str, sess.get("breed", "黑羽"))
            return date_picker_component(end_date), batch_list_component(batch_list)
    except Exception as e:
        return str(e)

@app.get("/reset")
def reset(sess:dict)-> Any:
    try:
        sess.clear()
        return Redirect("/batches")
    except Exception as e:
        return str(e)

@app.get("/content/{batch_name}/{tab_type}")
def content(batch_name: str, tab_type: str)-> Any:
    try:
        batch = cached_data.query_batch(batch_name)
        if not batch:
            return str(f"未找到批次 {batch_name}")
        if tab_type == "breed":
            return nav_tabs(batch, "breed"), breed_summary(batch), breed_table_component(batch)
        if tab_type == "sales":
            return nav_tabs(batch, "sales"), sales_summary(batch), sales_table_component(batch)
        if tab_type == "feed":
            return nav_tabs(batch, "feed"), feed_summary(batch), feed_table_component(batch)
    except Exception as e:
        return str(e)

if __name__ == "__main__":
    serve()
    
