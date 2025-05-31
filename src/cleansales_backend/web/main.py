from functools import cache, lru_cache
import uuid
from fasthtml.common import *
from postgrest.exceptions import APIError
from cleansales_backend.core.config import get_settings
from supabase import Client, create_client
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from cleansales_backend.domain.models.breed_record import BreedRecord
from cleansales_backend.domain.models.sale_record import SaleRecord
from cleansales_backend.domain.models.feed_record import FeedRecord
from cleansales_backend.domain.models.batch_aggregate import BatchAggregate, BatchAggregateModel
from cleansales_backend.domain.utils import week_age, day_age
from collections import defaultdict
import logging
from rich.logging import RichHandler

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
        self.batches: dict[str, tuple[BatchAggregate, datetime]] = {}

    def query_batch(self, batch_name: str) -> BatchAggregate | None:
        if batch_name in self.batches:
            cached_batch = self.batches.get(batch_name)
            if cached_batch and cached_batch[1] + timedelta(seconds=self.ALIVE_TIME) > datetime.now():
                return cached_batch[0]
        return self.query_single_batch_db(batch_name)

    def cached_batches(self) -> FT:
        return Ul(
            *[Li(P(batch[0]),P(batch[1])) for batch in self.batches.values()],
            name="cached_batches"
        )

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
            self.batches[batch_name] = (batch_aggregate, datetime.now())
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
                batch_aggregate = BatchAggregate(
                    breeds=breeds,
                    sales=sale_dict[batch_name],
                    feeds=feed_dict[batch_name],
                )
                batchaggr[batch_name] = batch_aggregate
                self.batches[batch_name] = batch_aggregate, datetime.now()

            return batchaggr
        except APIError as e:
            print(e)
            return {}
        except Exception as e:
            print(e)
            return {}

cached_data = CachedData(supabase)

app, rt = fast_app(live=True, secret_key="secret",session_cookie="batch_query", max_age=86400)

def breeds_selector_component(selected_breed: str)-> FT:
    # 雞種選項列表
    breeds = ['黑羽', '古早', '舍黑', '閹雞']
    
    # 建立雞種選擇器組件
    return Nav(
        Ul(Li(Strong(selected_breed))),
        Ul(
        *[
            Li(
                AX(
                breed, 
                # 設置 HTMX 屬性，使用 hx-swap="outerHTML" 來替換整個元件
                hx_get=f'/query_batches?breed={breed}',
            )) if breed != selected_breed else Li(Button(breed, cls="secondary"))
            for breed in breeds
        ],
        ),
        id="breeds_selector",  # 重要：設置 ID 來匹配 hx_target
        hx_swap_oob="true"
    )

def date_picker_component(end_date_str: str)-> FT:
    # 日期導航按鈕
    earlier_date_str = (datetime.strptime(end_date_str, '%Y-%m-%d') - timedelta(days=30)).strftime('%Y-%m-%d')
    earlier_btn = Button(
        "<<", 
        hx_get=f'/query_batches?end_date={earlier_date_str}', 
        cls="secondary outline"
    )
    
    later_date_str = (datetime.strptime(end_date_str, '%Y-%m-%d') + timedelta(days=30)).strftime('%Y-%m-%d')
    later_btn = Button(
        ">>", 
        hx_get=f'/query_batches?end_date={later_date_str}', 
        cls="secondary outline"
    )
    
    reset_btn = Button(
        "Reset", 
        type='reset',
        hx_get='/reset',
        cls="contrast"
    )
    
    # 日期輸入框
    date_input = Details(
        Summary(end_date_str, role="button"),
        Group(
            Input(
                type="date",
                aria_label="Date",
                name="end_date", 
                id="end_date", 
                value=end_date_str,
                hx_get='/query_batches',
                hx_trigger="change",
            ),
            reset_btn,
        ),
    )
    
    # 返回完整的選擇器元件
    return Group(earlier_btn, date_input, later_btn,
                id="date_picker", hx_swap_oob="true")

def breed_table_component(breeds: list[BreedRecord])-> FT:
    return Table(
        Thead(
            Tr(
                Th("種母場"),
                Th("入雛日"),
                Th("日齡"),
                Th("週齡"),
                Th("公數"),
                Th("母數"),
            )
        ),
        Tbody(
            Tr(
               Td(breed.supplier),
                Td(breed.breed_date.strftime('%Y-%m-%d')),
                Td(day_age(breed.breed_date)),
                Td(week_age(day_age(breed.breed_date))),
                Td(breed.breed_male),
                Td(breed.breed_female),
            )
            for breed in breeds
        ),
        Tfoot(
            Tr(
                Th("總和"),
                Th(),
                Th(),
                Th(),
                Th(sum(breed.breed_male for breed in breeds)),
                Th(sum(breed.breed_female for breed in breeds)),
            )
        )
    )


def sales_table_component(batch: BatchAggregate)-> FT | None:
    if not batch.sales:
        return None
    return Table(
        Thead(
            Tr(
                Th("日期"),
                Th("客戶"),
                Th("公數"),
                Th("母數"),
                Th("公重"),
                Th("母重"),
                Th("公價"),
                Th("母價"),
                Th("總重"),
                Th("均價"),
                Th("總收"),
            )
        ),
        Tbody(
            Tr(
                Td(sale.sale_date.strftime('%Y-%m-%d')),
                Td(sale.customer),
                Td(sale.male_count),
                Td(sale.female_count),
                Td(f'{sale.male_avg_weight:.2f}' if sale.male_avg_weight else ""),
                Td(f'{sale.female_avg_weight:.2f}' if sale.female_avg_weight else ""),
                Td(f'{sale.male_price:.1f}' if sale.male_price else ""),
                Td(f'{sale.female_price:.1f}' if sale.female_price else ""),
                Td(f'{sale.total_weight:.1f}' if sale.total_weight else ""),
                Td(f'{sale.avg_price:.1f}' if sale.avg_price else ""),
                Td(f'{int(sale.total_price):,}' if sale.total_price else ""),
            )
            for sale in sorted(batch.sales, key=lambda sale: sale.sale_date, reverse=True)
        ),
    )
    
    
def breed_summary(batch: BatchAggregate)-> FT:
    return Div(
        H4("飼養資料"),
        Ul(
            Li('管理人：' + batch.breeds[0].farmer_name if batch.breeds[0].farmer_name else ""),
            Li('供應商：' + batch.breeds[0].supplier if batch.breeds[0].supplier else ""),
            Li('獸醫：' + batch.breeds[0].veterinarian if batch.breeds[0].veterinarian else ""),
            Li('農場：' + batch.breeds[0].farm_name if batch.breeds[0].farm_name else ""),
            Li('地址：' + batch.breeds[0].address if batch.breeds[0].address else ""),
            Li('許可證號碼：' + batch.breeds[0].farm_license )if batch.breeds[0].farm_license else None,
        ),
        name="breed_summary"
    )

def sales_summary(batch: BatchAggregate)-> FT | None:
    if not batch.sales_summary:
        return None
    return Div(
        H4("銷售資料"),
        Ul(
            Li('成數：' + str(batch.sales_summary.sales_percentage*100).format("{:.2f}"+"%")),
            Li(
                '平均重量：' + str(batch.sales_summary.avg_weight).format("{:.2f}"+"斤"),
                Ul(
                    Li('平均公雞重量：' + str(batch.sales_summary.avg_male_weight).format("{:.2f}"+"斤")),
                    Li('平均母雞重量：' + str(batch.sales_summary.avg_female_weight).format("{:.2f}"+"斤")),
                ),
            ),
            Li(
                '平均單價：' + str(batch.sales_summary.avg_price_weight).format("{:.2f}"+"元"),
                Ul(
                    Li('平均公雞單價：' + str(batch.sales_summary.avg_male_price).format("{:.2f}"+"元")),
                    Li('平均母雞單價：' + str(batch.sales_summary.avg_female_price).format("{:.2f}"+"元")),
                ),
            ),
            Li('總銷售數量：' + str(batch.sales_summary.total_sales)),
            Li('開場最大日齡：' + str(batch.sales_summary.sales_open_close_dayage[0])),
            Li('結案最小日齡：' + str(batch.sales_summary.sales_open_close_dayage[1])),
            Li('總營收：' + f"{int(batch.sales_summary.total_revenue):,}元"),
        ),
        name="sales_summary"
    )
    

def batch_list_component(batch_list: dict[str, BatchAggregate])-> FT:
    def _sales_progress_component(batch: BatchAggregate)-> FT | None:
        if batch.sales_percentage:
            return Progress(value=batch.sales_percentage, max=1)
        return None


    def nav_tabs(batch: BatchAggregate)-> FT:
        # 使用 batch.safe_id 作為 CSS 選擇器，這是一個安全的 ID 格式
        breed_tab = Li(
            Button(
                "飼養資料",
                hx_get=f'/content/{batch.batch_name}/breed',
                hx_target=f"#{batch.safe_id}_batch_tab_content",
            ) if batch.breeds else None
        )
        sales_tab = Li(
            Button(
                "銷售資料",
                hx_get=f'/content/{batch.batch_name}/sales',
                hx_target=f"#{batch.safe_id}_batch_tab_content",
            ) if batch.sales else None
        )
        return Nav(
            Ul(
                breed_tab,
                sales_tab,
            ),
            id="batch_nav_tabs"
        )

    
    
    # 如果沒有批次數據，顯示空狀態
    if not batch_list:
        return Div(
            Article(
                H3("沒有找到符合條件的批次記錄")
            ),
            id="batch_list", hx_swap_oob="true"
        )

    
    # 返回批次列表
    return Div(*[
                Details(
                    Summary(batch.batch_name, _sales_progress_component(batch)),
                    Card(
                        nav_tabs(batch),
                        # _sales_summary(batch),
                        Div(
                            breed_summary(batch),
                            breed_table_component(batch.breeds),
                            id=f"{batch.safe_id}_batch_tab_content"),
                        ),
                    open=False,
                    cls="outline"
                )
                for batch in sorted(batch_list.values(), key=lambda x: x.breeds[0].breed_date)
            ], id="batch_list", hx_swap_oob="true"
            )

@app.get("/batches")
def batches(sess:dict)-> Any:
    try:
        breed = sess.get("breed", "黑羽")
        end_date_str = sess.get("end_date", datetime.now().strftime('%Y-%m-%d'))
        start_date_str = (datetime.strptime(end_date_str, '%Y-%m-%d') - timedelta(days=30)).strftime('%Y-%m-%d')
        batch_list = cached_data.query_batches_db(start_date_str, end_date_str, breed)
        return Main(
            # 使用 PicoCSS 的容器和標題
            H1("雞隻批次查詢系統", cls="text-center"),
            # 使用元件
            breeds_selector_component(breed),
            date_picker_component(end_date_str),
            batch_list_component(batch_list),
            # 使用 container 類來適應深色/淺色主題
            cls="container"
        ),Footer(P(f"{cached_data.query_batches_db.cache_info()}", cls="text-center"),cached_data.cached_batches())
    except APIError as e:
        return Main(
            Article(
                H1("資料庫查詢錯誤"),
                P(str(e)),
                cls="error"
            ),
            cls="container"
        )
    except Exception as e:
        return Main(
            Article(
                H1("發生錯誤"),
                P(str(e)),
                cls="error"
            ),
            cls="container"
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
            return breed_summary(batch), breed_table_component(batch.breeds)
        if tab_type == "sales":
            return sales_summary(batch), sales_table_component(batch)
    except Exception as e:
        return str(e)

if __name__ == "__main__":
    serve()
    
