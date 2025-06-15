import json
from turtle import title
from fasthtml.common import *

from cleansales_backend.core.config import get_settings
from cleansales_backend.web.data_service import SQLiteDataService
from cleansales_backend.web.file_upload_handler import DB_PATH
from cleansales_backend.web.resources import common_headers

app, rt = fast_app(
    live=get_settings().WEB_LIVE,
    key_fname=".sesskey",
    session_cookie="cleansales",
    max_age=86400,
    hdrs=(common_headers),
    pico=False,
)

base_layout = lambda x: (Title("Cleansales"), Body(x, cls="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 p-6"))
breeds = [('黑羽', '黑羽', 'batches/黑羽'),
          ('古早', '古早', 'batches/古早'),
          ('舍黑', '舍黑', 'batches/舍黑'),
          ('閹雞', '閹雞', 'batches/閹雞')]
breeds_nav= lambda title, value, herf: Li(
    Button(title, hx_get=herf, hx_include="#start_date", hx_target="#load_batches", cls="text-lg font-semibold cursor-pointer bg-white text-gray-700 px-6 py-3 rounded-xl shadow-md hover:shadow-lg hover:bg-blue-50 hover:text-blue-600 transition-all duration-200 border border-gray-200"))
nav_tabs = Ul(*[breeds_nav(title, value, herf) for title, value, herf in breeds],
            cls="flex flex-row justify-center gap-4 mb-8 p-6 bg-white rounded-2xl shadow-lg")
@rt('/')
def index():
    from datetime import datetime
    today = datetime.now().strftime('%Y-%m-%d')
    
    header = Div(
        H1("Cleansales 批次管理", cls="text-4xl font-bold text-gray-800 text-center mb-2"),
        P("管理養雞場批次資料", cls="text-gray-600 text-center mb-4"),
        cls="mb-6"
    )
    
    date_selector = Div(
        Label("選擇起始日期：", cls="block text-sm font-medium text-gray-700 mb-2"),
        Input(
            type="date", 
            id="start_date", 
            value=today,
            cls="px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
        ),
        Button(
            "更新", 
            hx_get="batches/黑羽",
            hx_include="#start_date",
            hx_target="#load_batches",
            cls="ml-2 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500"
        ),
        cls="flex items-center justify-center mb-6 p-4 bg-white rounded-lg shadow-sm"
    )
    
    load_batches = Div(id="load_batches", hx_get="batches/黑羽", hx_target="#load_batches", hx_trigger='load', cls="container mx-auto")
    return base_layout((header, date_selector, nav_tabs, load_batches))


@rt('/batches/{breed}')
def query_batches(breed:str, start_date: str|None = None):
    from datetime import datetime, timedelta
    
    breed = breed.strip()
    if breed == "":
        breed = '黑羽'
    
    # 設定起始查找日期為今天，如果沒有提供start_date的話
    if start_date is None:
        today = datetime.now().date()
        start_date = today.strftime('%Y-%m-%d')
    else:
        today = datetime.strptime(start_date, '%Y-%m-%d').date()
    
    # 計算結束日期（30天前）
    end_date = (today - timedelta(days=30)).strftime('%Y-%m-%d')
    stmt = """
        SELECT 
        subquery.batch_name as batch_name,
        subquery.chicken_breed as chicken_breed,
        subquery.breed_date as breed_date,
        subquery.expire_date as expire_date,
        subquery.total_breed as total_breed,
        COALESCE(sale.total_count, 0) AS total_count,
        CASE 
            WHEN subquery.total_breed > 0 THEN (COALESCE(sale.total_count, 0) * 100.0 / subquery.total_breed)  -- 計算百分比
            ELSE 0  -- 如果 total_breed 為 0，則百分比設為 0
        END as percentage,
        COALESCE(farm.fcr, 0) AS fcr
    FROM
        (
            SELECT
                batch_name,
                chicken_breed,
                MIN(breed_date) AS breed_date,
                DATE(MIN(breed_date), "+119 days") AS expire_date,
                SUM(breed_male + breed_female) AS total_breed
            FROM
                breed
            GROUP BY
                batch_name, chicken_breed
        ) AS subquery
    LEFT JOIN (
        SELECT
            batch_name,
            SUM(male_count + female_count) AS total_count
        FROM
            sale
        GROUP BY
            batch_name
    ) AS sale ON subquery.batch_name = sale.batch_name
    LEFT JOIN (
        SELECT
            batch_name,
            fcr
        FROM
            farm_production
    ) AS farm ON subquery.batch_name = farm.batch_name
    WHERE
        subquery.chicken_breed = ?
        AND subquery.breed_date <= ?
        AND subquery.expire_date >= ?
    ORDER BY
        subquery.expire_date DESC
    """
    def _render_batches(data):
        percentage = round(data['percentage'], 1)
        percentage_color = "text-green-600" if percentage >= 80 else "text-yellow-600" if percentage >= 50 else "text-red-600"
        fcr = round(data['fcr'], 2) if data['fcr'] else 0
        fcr_color = "text-green-600" if fcr <= 2.6 else "text-yellow-600" if fcr <= 3.0 else "text-red-600"
        
        return Card(
            Div(
                Div(
                    H3(data['batch_name'], cls="text-xl font-bold text-gray-800 mb-2"),
                    Span(data['chicken_breed'], cls="inline-block bg-blue-100 text-blue-800 px-3 py-1 rounded-full text-sm font-medium"),
                    cls="flex justify-between items-start mb-4"
                ),
                
                Div(
                    Div(
                        P("飼養日期", cls="text-sm text-gray-500 mb-1"),
                        P(data['breed_date'], cls="font-semibold text-gray-700"),
                        cls="flex flex-col"
                    ),
                    Div(
                        P("到期日期", cls="text-sm text-gray-500 mb-1"),
                        P(data['expire_date'], cls="font-semibold text-gray-700"),
                        cls="flex flex-col"
                    ),
                    cls="grid grid-cols-2 gap-4 mb-4"
                ),
                
                Div(
                    Div(
                        P("總飼養數", cls="text-sm text-gray-500 mb-1"),
                        P(f"{data['total_breed']:,}", cls="text-lg font-bold text-gray-800"),
                        cls="text-center"
                    ),
                    Div(
                        P("已售出數", cls="text-sm text-gray-500 mb-1"),
                        P(f"{data['total_count']:,}", cls="text-lg font-bold text-gray-800"),
                        cls="text-center"
                    ),
                    Div(
                        P("銷售率", cls="text-sm text-gray-500 mb-1"),
                        P(f"{percentage}%", cls=f"text-2xl font-bold {percentage_color}"),
                        cls="text-center"
                    ),
                    Div(
                        P("FCR", cls="text-sm text-gray-500 mb-1"),
                        P(f"{fcr}" if fcr > 0 else "N/A", cls=f"text-lg font-bold {fcr_color}"),
                        cls="text-center"
                    ),
                    cls="grid grid-cols-4 gap-4 mb-4"
                ),
                
                Div(
                    Div(cls=f"h-2 bg-gray-200 rounded-full overflow-hidden"),
                    Div(cls=f"h-2 bg-gradient-to-r from-blue-400 to-blue-600 rounded-full transition-all duration-300", style=f"width: {min(percentage, 100)}%"),
                    cls="relative"
                ),
                
                cls="p-6"
            ),
            cls="bg-white rounded-xl shadow-md hover:shadow-lg transition-shadow duration-200 mb-4 border border-gray-100"
        )
    # 查詢當前30天的資料
    params = (breed, end_date, start_date)
    
    # 查詢下一個30天區間是否有資料
    next_start_date = (today - timedelta(days=30)).strftime('%Y-%m-%d')
    next_end_date = (today - timedelta(days=60)).strftime('%Y-%m-%d')
    next_params = (breed, next_end_date, next_start_date)
    
    sql_service = SQLiteDataService(DB_PATH)
    conn = sql_service.get_db_connection()
    cursor = conn.cursor()
    cursor.execute(stmt, params)
    data = cursor.fetchall()
    cursor.execute(stmt, next_params)
    has_more = True if cursor.fetchone() else False
    # df = pd.DataFrame([dict(row) for row in data][::-1])
    # df = df.iloc[::-1]
    # print(df.head())
    load_more_btn = Div(
        Button("載入更多", 
               id='load_order', 
               hx_get=f'batches/{breed}',
               hx_vals=json.dumps({'start_date': next_start_date}),
               hx_target='#load_order', 
               hx_swap='outerHTML',
               cls="w-full bg-blue-600 hover:bg-blue-700 text-white font-semibold py-3 px-6 rounded-xl shadow-md hover:shadow-lg transition-all duration-200 mb-6"
        ),
        cls="text-center"
    ) if has_more else Div()
    
    batches_container = Div(
        *[_render_batches(dict(row)) for row in data][::-1],
        cls="grid gap-4"
    )
    
    return (load_more_btn, batches_container)
    