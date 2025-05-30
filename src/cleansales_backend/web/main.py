from fasthtml.common import *
from postgrest.exceptions import APIError
from cleansales_backend.core.config import get_settings
from supabase import Client, create_client
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from cleansales_backend.domain.models.breed_record import BreedRecord
from cleansales_backend.domain.utils import week_age, day_age

supabase: Client = create_client(
    supabase_url=get_settings().SUPABASE_CLIENT_URL,
    supabase_key=get_settings().SUPABASE_ANON_KEY,
)

@dataclass
class BatchAggregates:
    batch_name: str
    breeds: list[BreedRecord] = field(init=False)
    farm_name: str = field(init=False)
    address: str = field(init=False)
    farmer_name: str = field(init=False)
    veterinarian: str = field(init=False)
    supplier: str = field(init=False)
    chicken_breed: list[str] = field(init=False)
    sub_location: list[str] = field(init=False)
    breed_date: list[datetime] = field(init=False)
    breed_male: list[int] = field(init=False)
    breed_female: list[int] = field(init=False)
    updated_at: list[datetime] = field(init=False)
    day_age: list[int] = field(init=False)
    week_age: list[str] = field(init=False)
    

    def __post_init__(self):
        response = supabase.table("breedrecordorm").select("*")\
            .eq("batch_name", self.batch_name)\
            .order("breed_date")\
            .execute()
        self.breeds = [BreedRecord.model_validate(data) for data in response.data]
        self.farm_name = self.breeds[0].farm_name if self.breeds and self.breeds[0].farm_name else ""
        self.address = self.breeds[0].address if self.breeds and self.breeds[0].address else ""
        self.farmer_name = self.breeds[0].farmer_name if self.breeds and self.breeds[0].farmer_name else ""
        self.veterinarian = self.breeds[0].veterinarian if self.breeds and self.breeds[0].veterinarian else ""
        self.supplier = self.breeds[0].supplier if self.breeds and self.breeds[0].supplier else ""
        self.chicken_breed = [breed.chicken_breed for breed in self.breeds]
        self.sub_location = [breed.sub_location if breed.sub_location else "" for breed in self.breeds]
        self.breed_date = [breed.breed_date for breed in self.breeds]
        self.breed_male = [breed.breed_male for breed in self.breeds]
        self.breed_female = [breed.breed_female for breed in self.breeds]
        self.updated_at = [breed.updated_at for breed in self.breeds]
        self.day_age = [day_age(breed.breed_date) for breed in self.breeds]
        self.week_age = [week_age(day_age) for day_age in self.day_age]

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
        "<< 往前30天", 
        hx_get=f'/query_batches?end_date={earlier_date_str}', 
        cls="secondary outline"
    )
    
    later_date_str = (datetime.strptime(end_date_str, '%Y-%m-%d') + timedelta(days=30)).strftime('%Y-%m-%d')
    later_btn = Button(
        "往後30天 >>", 
        hx_get=f'/query_batches?end_date={later_date_str}', 
        cls="secondary outline"
    )
    
    reset_btn = Button(
        "重置篩選", 
        hx_get='/reset',
        cls="contrast"
    )
    
    # 日期輸入框
    date_input = Input(
        type="date", 
        name="end_date", 
        id="end_date", 
        value=end_date_str,
        hx_get='/query_batches',
        hx_trigger="change",
        style="width: 200px;"
    )
    
    # 返回完整的選擇器元件
    return Group(date_input, earlier_btn, reset_btn, later_btn,
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

def batch_list_component(chicken_breed: str, end_date_str: str)-> FT:
    # 計算日期範圍
    start_date = (datetime.strptime(end_date_str, '%Y-%m-%d') - timedelta(days=30)).strftime('%Y-%m-%d')
    
    # 查詢批次數據
    response = supabase.table("batchaggregates").select("*")\
        .eq("chicken_breed", chicken_breed)\
        .gte("final_date", start_date)\
        .lte("initial_date", end_date_str)\
        .order("initial_date")\
        .execute()
    
    # 將批次數據轉換為 BatchAggregates 對象
    batch_list = [BatchAggregates(batch_name=data['batch_name']) for data in response.data]
    
    # 如果沒有批次數據，顯示空狀態
    if not batch_list:
        return Div(
            Article(
                H3(f"沒有找到符合條件的 {chicken_breed} 批次記錄"),
                P(f"日期範圍: {start_date} 至 {end_date_str}"),
                cls="warning"
            ),
            id="batch_list", hx_swap_oob="true"
        )
    
    # 返回批次列表
    return Div(*[
                Details(
                    Summary(
                        H4(batch.batch_name),
                        Div(
                            Label(f'週齡: {"~".join(batch.week_age)}'),
                            Label(f'公雞數: {sum(batch.breed_male)}'), 
                            Label(f'母雞數: {sum(batch.breed_female)}'),
                            style="margin-top: 5px; display: flex; gap: 10px;"
                        ),
                        style="display: flex; flex-direction: column; cursor: pointer; padding: 10px;"
                    ),
                    Article(
                        Div(
                            Span(batch.farm_name, style="font-weight: bold; margin-right: 10px;"), 
                            Span(batch.address), 
                            Span(batch.farmer_name, style="margin-left: 10px; font-style: italic;"),
                            style="margin-bottom: 8px;"
                        ),
                        Div(
                            Span(f'獸醫: {batch.veterinarian}', style="margin-right: 15px;"), 
                            Span(f'供應商: {batch.supplier}'),
                            style="margin-bottom: 8px;"
                        ),
                        Div(
                            *[P(f"{date.strftime('%Y-%m-%d')} ({age} 天)") 
                              for date, age in zip(batch.breed_date, batch.day_age)],
                            style="display: flex; flex-direction: column;"
                        ),
                        breed_table_component(batch.breeds),
                    ),
                    open=False,
                    cls="outline"
                )
                for batch in batch_list
            ], id="batch_list", hx_swap_oob="true"
            )

@app.get("/batches")
def batches(sess:dict)-> Any:
    try:
        breed = sess.get("breed", "黑羽")
        end_date_str = sess.get("end_date", datetime.now().strftime('%Y-%m-%d'))    
        return Main(
            # 使用 PicoCSS 的容器和標題
            H1("雞隻批次查詢系統", cls="text-center"),
            # 使用元件
            breeds_selector_component(breed),
            date_picker_component(end_date_str),
            batch_list_component(breed, end_date_str),
            # 使用 container 類來適應深色/淺色主題
            cls="container"
        )
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
            return breeds_selector_component(breed), batch_list_component(breed, sess.get("end_date", datetime.now().strftime('%Y-%m-%d')))
        if end_date:
            sess["end_date"] = end_date
            return date_picker_component(end_date), batch_list_component(sess.get("breed", "黑羽"), end_date)
    except Exception as e:
        return str(e)

@app.get("/reset")
def reset(sess:dict)-> Any:
    try:
        sess.clear()
        return Redirect("/batches")
    except Exception as e:
        return str(e)

serve()