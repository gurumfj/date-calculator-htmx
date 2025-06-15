import json

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
    Button(title, 
           hx_get=herf, 
           hx_include="#start_date", 
           hx_target="#load_batches", 
           hx_swap="innerHTML transition:true",
           **{"@click": f"activeBreed = '{value}'"},
           **{":class": f"activeBreed === '{value}' ? 'text-lg font-semibold cursor-pointer bg-blue-600 text-white px-6 py-3 rounded-xl shadow-lg border border-blue-600' : 'text-lg font-semibold cursor-pointer bg-white text-gray-700 px-6 py-3 rounded-xl shadow-md hover:shadow-lg hover:bg-blue-50 hover:text-blue-600 border border-gray-200'"},
           cls="transition-all duration-200"))
@rt('/')
def index():
    from datetime import datetime
    today = datetime.now().strftime('%Y-%m-%d')
    
    header = Div(
        H1("Cleansales 批次管理", cls="text-4xl font-bold text-gray-800 text-center mb-2"),
        P("管理養雞場批次資料", cls="text-gray-600 text-center mb-4"),
        cls="mb-6"
    )
    
    # 合併導航區域，包含品種選擇和日期選擇
    nav_section = Nav(
        # 品種選擇 - 總是可見
        Header(
            Div(
                H4("選擇品種", cls="text-sm font-medium text-gray-700 mb-3 text-center"),
                Ul(*[breeds_nav(title, value, herf) for title, value, herf in breeds],
                   cls="flex flex-row justify-center gap-4"),
                cls="mb-4"
            ),
            
            # 展開/收合日期選擇的按鈕
            Div(
                Button(
                    Span("進階篩選", cls="mr-2"),
                    Span("▼", cls="transform transition-transform duration-200 inline-block",
                         **{":class": "datePickerOpen ? 'rotate-180' : 'rotate-0'"}),
                    **{"@click": "datePickerOpen = !datePickerOpen"},
                    cls="text-sm text-gray-600 hover:text-gray-800 focus:outline-none transition-colors duration-200"
                ),
                cls="text-center"
            ),
            cls="cursor-pointer"
        ),
        
        # 日期選擇 - 可展開收合
        Section(
            Div(
                H4("選擇起始日期", cls="text-sm font-medium text-gray-700 mb-3 text-center"),
                Div(
                    Input(
                        type="date", 
                        id="start_date", 
                        value=today,
                        cls="px-4 py-2 border border-gray-300 rounded-lg shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                    ),
                    Button(
                        "更新", 
                        **{
                            "hx-get": "",
                            ":hx-get": "`batches/${activeBreed}`",
                            "hx-include": "#start_date",
                            "hx-target": "#load_batches",
                            "hx-swap": "innerHTML transition:true"
                        },
                        cls="ml-3 px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 transition-colors duration-200"
                    ),
                    cls="flex items-center justify-center gap-2"
                )
            ),
            cls="pt-4 border-t border-gray-100 transition-all duration-300 ease-out overflow-hidden",
            **{
                ":style": "datePickerOpen ? 'max-height: 200px; opacity: 1;' : 'max-height: 0px; opacity: 0; padding-top: 0;'"
            }
        ),
        
        cls="bg-white rounded-2xl shadow-lg p-6 mb-8"
    )
    
    load_batches = Div(id="load_batches", hx_get="batches/黑羽", hx_target="#load_batches", hx_trigger='load', hx_swap="innerHTML transition:true", cls="container mx-auto transition-opacity duration-300")
    
    # 將所有元件包在一個 Alpine.js 容器中
    app_container = Div(
        header, nav_section, load_batches,
        **{"x-data": "{ activeBreed: '黑羽', datePickerOpen: false }"}
    )
    
    return base_layout(app_container)


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
        
        # 計算顯示的資料項目（預留最多5個grid空間）
        data_items = [
            {"label": "飼養日期", "value": data['breed_date'], "color": "text-gray-800"},
            {"label": "到期日期", "value": data['expire_date'], "color": "text-gray-800"},
            {"label": "總飼養數", "value": f"{data['total_breed']:,}", "color": "text-gray-800"},
            {"label": "銷售率", "value": f"{percentage}%", "color": percentage_color},
            {"label": "FCR", "value": f"{fcr}" if fcr > 0 else "N/A", "color": fcr_color},
        ]
        
        return Article(
            # 上半部 - 摘要資訊區域
            Header(
                Div(
                    H3(data['batch_name'], cls="text-xl font-bold text-gray-800"),
                    Span(data['chicken_breed'], cls="inline-block bg-blue-100 text-blue-800 px-3 py-1 rounded-full text-sm font-medium"),
                    cls="flex justify-between items-center mb-4"
                ),
                
                # 動態資料顯示區域（最多5個grid）
                Div(
                    *[
                        Div(
                            P(item["value"], cls=f"text-lg font-bold {item['color']}"),
                            P(item["label"], cls="text-xs text-gray-500"),
                            cls="text-center"
                        ) for item in data_items
                    ],
                    Div(
                        # 展開/收合圖示
                        Span("▼", cls="text-gray-400 transform transition-transform duration-200 inline-block", 
                             **{":class": "open ? 'rotate-180' : 'rotate-0'"}),
                        cls="flex items-center justify-center"
                    ),
                    cls="grid grid-cols-6 gap-2 items-center"
                ),
                cls="p-4 cursor-pointer",
                **{"@click": "open = !open"}
            ),
            
            # 下半部 - 詳細資訊區域（預留給其他查詢路由）
            Section(
                # Mock 資料 UI
                Div(
                    H4("詳細資訊", cls="text-lg font-semibold text-gray-800 mb-4"),
                    
                    # 飼養詳情
                    Details(
                        Summary("飼養詳情", cls="cursor-pointer font-medium text-gray-700 mb-2"),
                        Div(
                            Div(
                                Span("雄雞數量", cls="text-sm text-gray-500"),
                                Span("1,200", cls="font-semibold text-gray-800"),
                                cls="flex justify-between py-1"
                            ),
                            Div(
                                Span("雌雞數量", cls="text-sm text-gray-500"),
                                Span("1,800", cls="font-semibold text-gray-800"),
                                cls="flex justify-between py-1"
                            ),
                            Div(
                                Span("平均重量", cls="text-sm text-gray-500"),
                                Span("2.5kg", cls="font-semibold text-gray-800"),
                                cls="flex justify-between py-1"
                            ),
                            cls="bg-gray-50 rounded-lg p-3 mb-4"
                        )
                    ),
                    
                    # 銷售記錄
                    Details(
                        Summary("銷售記錄", cls="cursor-pointer font-medium text-gray-700 mb-2"),
                        Div(
                            Table(
                                Thead(
                                    Tr(
                                        Th("日期", cls="text-left py-2 px-3 text-sm font-medium text-gray-500"),
                                        Th("數量", cls="text-left py-2 px-3 text-sm font-medium text-gray-500"),
                                        Th("單價", cls="text-left py-2 px-3 text-sm font-medium text-gray-500"),
                                        Th("金額", cls="text-left py-2 px-3 text-sm font-medium text-gray-500"),
                                    )
                                ),
                                Tbody(
                                    Tr(
                                        Td("2024-12-01", cls="py-2 px-3 text-sm text-gray-800"),
                                        Td("150", cls="py-2 px-3 text-sm text-gray-800"),
                                        Td("85", cls="py-2 px-3 text-sm text-gray-800"),
                                        Td("12,750", cls="py-2 px-3 text-sm text-gray-800"),
                                    ),
                                    Tr(
                                        Td("2024-12-15", cls="py-2 px-3 text-sm text-gray-800"),
                                        Td("200", cls="py-2 px-3 text-sm text-gray-800"),
                                        Td("88", cls="py-2 px-3 text-sm text-gray-800"),
                                        Td("17,600", cls="py-2 px-3 text-sm text-gray-800"),
                                    ),
                                    cls="divide-y divide-gray-200"
                                ),
                                cls="min-w-full bg-white rounded-lg"
                            ),
                            cls="bg-gray-50 rounded-lg p-3 overflow-x-auto"
                        )
                    ),
                    
                    # 生產分析
                    Details(
                        Summary("生產分析", cls="cursor-pointer font-medium text-gray-700 mb-2"),
                        Div(
                            Div(
                                Canvas(id=f"chart-{data['batch_name']}", cls="w-full h-32"),
                                P("生產效率趨勢圖", cls="text-center text-sm text-gray-500 mt-2"),
                                cls="bg-gray-50 rounded-lg p-4"
                            )
                        )
                    )
                ),
                cls="px-4 pb-4 border-t border-gray-100 transition-all duration-300 ease-out overflow-hidden",
                **{
                    ":style": "open ? 'max-height: 1000px; opacity: 1;' : 'max-height: 0px; opacity: 0; padding-top: 0; padding-bottom: 0;'"
                }
            ),
            
            cls="bg-white rounded-xl shadow-md hover:shadow-lg transition-shadow duration-200 mb-4 border border-gray-100",
            **{"x-data": "{ open: false }"}
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
               hx_swap='outerHTML transition:true',
               cls="w-full bg-blue-600 hover:bg-blue-700 text-white font-semibold py-3 px-6 rounded-xl shadow-md hover:shadow-lg transition-all duration-200 mb-6"
        ),
        cls="text-center"
    ) if has_more else Div()
    
    batches_container = Div(
        *[_render_batches(dict(row)) for row in data][::-1],
        cls="grid gap-4"
    )
    
    return (load_more_btn, batches_container)
    