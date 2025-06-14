import json
import logging
from datetime import datetime
import hashlib
import sqlite3
import pandas as pd
from io import BytesIO
import time
import uuid

from cleansales_backend.core.config import get_settings
from fasthtml.common import *
from cleansales_backend.web.resources import alpine_cdn
from cleansales_backend.processors.breeds_schema import BreedRecordValidator
from cleansales_backend.processors.sales_schema import SaleRecordValidator
from cleansales_backend.processors.feeds_schema import FeedRecordValidator

logger = logging.getLogger(__name__)
DB_PATH = "./data/sqlite.db"


def get_db_connection():
    """獲取數據庫連接"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def log_upload_event(
    event_id: str,
    file_name: str,
    file_size: int,
    file_type: str,
    processing_status: str,
    processing_time_ms: int,
    valid_count: int = 0,
    invalid_count: int = 0,
    duplicates_removed: int = 0,
    inserted_count: int = 0,
    deleted_count: int = 0,
    duplicate_count: int = 0,
    error_message: str | None = None,
    metadata: dict | None = None
) -> str:
    """記錄上傳事件到數據庫"""
    conn = get_db_connection()
    try:
        conn.execute("""
            INSERT INTO upload_events (
                event_id, file_type, file_name, file_size, processing_status,
                valid_count, invalid_count, duplicates_removed, inserted_count,
                deleted_count, duplicate_count, error_message, processing_time_ms,
                metadata
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            event_id, file_type, file_name, file_size, processing_status,
            valid_count, invalid_count, duplicates_removed, inserted_count,
            deleted_count, duplicate_count, error_message, processing_time_ms,
            json.dumps(metadata) if metadata else None
        ))
        conn.commit()
        return event_id
    except Exception as e:
        logger.error(f"記錄上傳事件失敗: {e}")
        return ""
    finally:
        conn.close()

def init_db():
    """初始化數據庫表"""
    conn = get_db_connection()
    try:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS breed (
                unique_id TEXT PRIMARY KEY,
                farm_name TEXT NOT NULL,
                address TEXT,
                farm_license TEXT,
                farmer_name TEXT,
                farmer_address TEXT,
                batch_name TEXT NOT NULL,
                sub_location TEXT,
                veterinarian TEXT,
                is_completed INTEGER DEFAULT 0,
                chicken_breed TEXT NOT NULL,
                breed_date TEXT NOT NULL,
                supplier TEXT,
                breed_male INTEGER DEFAULT 0,
                breed_female INTEGER DEFAULT 0,
                event_id TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
            
            CREATE TABLE IF NOT EXISTS feed (
                unique_id TEXT PRIMARY KEY,
                batch_name TEXT NOT NULL,
                feed_date TEXT NOT NULL,
                feed_manufacturer TEXT NOT NULL,
                feed_item TEXT NOT NULL,
                sub_location TEXT,
                is_completed INTEGER DEFAULT 0,
                feed_week TEXT,
                feed_additive TEXT,
                feed_remark TEXT,
                event_id TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
            
            CREATE TABLE IF NOT EXISTS sale (
                unique_id TEXT PRIMARY KEY,
                is_completed INTEGER DEFAULT 0,
                handler TEXT,
                sale_date TEXT NOT NULL,
                batch_name TEXT NOT NULL,
                customer TEXT NOT NULL,
                male_count INTEGER DEFAULT 0,
                female_count INTEGER DEFAULT 0,
                total_weight REAL,
                total_price REAL,
                male_price REAL,
                female_price REAL,
                unpaid INTEGER DEFAULT 1,
                event_id TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
            
            CREATE TABLE IF NOT EXISTS upload_events (
                event_id TEXT PRIMARY KEY,
                file_type TEXT NOT NULL,
                file_name TEXT NOT NULL,
                file_size INTEGER NOT NULL,
                upload_timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
                processing_status TEXT DEFAULT 'completed',
                valid_count INTEGER DEFAULT 0,
                invalid_count INTEGER DEFAULT 0,
                duplicates_removed INTEGER DEFAULT 0,
                inserted_count INTEGER DEFAULT 0,
                deleted_count INTEGER DEFAULT 0,
                duplicate_count INTEGER DEFAULT 0,
                error_message TEXT,
                processing_time_ms INTEGER,
                user_agent TEXT,
                ip_address TEXT,
                metadata TEXT
            );
        """)
        conn.commit()
    except Exception as e:
        logger.error("創建數據表失敗: %s", str(e))
    finally:
        conn.close()
init_db()

app, rt = fast_app(
    live=get_settings().WEB_LIVE,
    key_fname=".sesskey",
    session_cookie="cleansales",
    max_age=86400,
    static_path='static',
    surreal=False,
    hdrs=(alpine_cdn,))

upload_breeds_form = Form(
    Label("Upload Breeds", Input(type="file", name="file", accept=".xlsx, .xls")),
    Button("Upload", type="submit"),
    enctype="multipart/form-data",
    hx_post="/upload/breeds",
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

def render_table(df: pd.DataFrame, current_column: str | None = None, current_order: str = "DESC", page: int = 0, page_size: int = 50, enable_event_links: bool = False):
    headers = df.columns
    
    # 分頁處理
    start_idx = page * page_size
    end_idx = start_idx + page_size
    rows = df.values[start_idx:end_idx]
    
    def create_header(header):
        # 決定下一次點擊的排序方向
        next_order = "ASC" if current_column == header and current_order == "DESC" else "DESC"
        
        # 顯示排序指示器
        indicator = ""
        if current_column == header:
            indicator = " ↓" if current_order == "DESC" else " ↑"
        
        return Th(
            header + indicator,
            hx_get='/q',
            hx_vals=json.dumps({"column": header, "order": next_order}),
            hx_target="#result",
            style="cursor: pointer;"
        )
    
    # 創建表格行
    table_rows = []
    for i, row in enumerate(rows):
        cells = []
        for j, (header, cell) in enumerate(zip(headers, row)):
            if enable_event_links and header == 'event_id' and cell:
                # 為event_id創建連結
                cells.append(Td(A(f"{str(cell)[:8]}...", href=f"/event/{cell}", style="color: #007bff; text-decoration: underline;")))
            else:
                cells.append(Td(str(cell)))
        table_rows.append(Tr(*cells, id=f"row-{start_idx + i}"))
    
    
    # 如果還有更多數據，添加加載觸發器
    if end_idx < len(df):
        load_more_trigger = Tr(
            Td(
                "載入更多...",
                colspan=len(headers),
                style="text-align: center; padding: 20px; color: #666;",
                hx_get='/load_more',
                hx_vals=json.dumps({
                    "column": current_column or "",
                    "order": current_order,
                    "page": page + 1
                }),
                hx_target="this",
                hx_swap="outerHTML",
                hx_trigger="revealed"
            ),
            id=f"load-trigger-{page + 1}"
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

def get_all_breeds():
    """獲取所有品種記錄"""
    conn = get_db_connection()
    try:
        cursor = conn.execute("SELECT * FROM breed ORDER BY breed_date DESC")
        return cursor.fetchall()
    finally:
        conn.close()

def detect_file_type(df: pd.DataFrame) -> str:
    """根據欄位名稱檢測檔案類型"""
    columns = set(df.columns.str.strip())
    
    # 檢查入雛記錄的特徵欄位
    breed_indicators = {"畜牧場名", "入雛日期", "雞種", "種雞場"}
    if breed_indicators.intersection(columns):
        return "breed"
    
    # 檢查銷售記錄的特徵欄位
    sale_indicators = {"客戶名稱", "公-隻數", "母-隻數", "總價"}
    if sale_indicators.intersection(columns):
        return "sale"
    
    # 檢查飼料記錄的特徵欄位
    feed_indicators = {"飼料廠", "品項", "周齡"}
    if feed_indicators.intersection(columns):
        return "feed"
    
    return "unknown"

async def process_upload(file: UploadFile):
    """處理上傳檔案的核心邏輯，支援三種類型（簡化版）"""
    start_time = time.time()
    event_id = str(uuid.uuid4())  # 提前生成event_id
    
    # 讀取上傳的文件內容
    filebuffer = await file.read()
    file_size = len(filebuffer)
    bytes_io = BytesIO(filebuffer)
    df = pd.read_excel(bytes_io)
    
    # 檢測檔案類型
    file_type = detect_file_type(df)
    
    if file_type == "unknown":
        processing_time_ms = int((time.time() - start_time) * 1000)
        log_upload_event(
            event_id=event_id,
            file_name=file.filename or "unknown",
            file_size=file_size,
            file_type=file_type,
            processing_status="failed",
            processing_time_ms=processing_time_ms,
            error_message="無法識別檔案類型",
            metadata={"columns": list(df.columns)}
        )
        return {
            "success": False,
            "message": "無法識別檔案類型，請確認欄位名稱是否正確",
            "file_type": file_type,
            "valid_count": 0,
            "invalid_count": 0,
            "data": []
        }
    
    # 根據檔案類型選擇相應的驗證器和表格
    validators = {
        "breed": (BreedRecordValidator, "breed", ["unique_id", "farm_name", "address", "farm_license", "farmer_name", "farmer_address", "batch_name", "sub_location", "veterinarian", "is_completed", "chicken_breed", "breed_date", "supplier", "breed_male", "breed_female", "event_id", "created_at"]),
        "sale": (SaleRecordValidator, "sale", ["unique_id", "is_completed", "handler", "sale_date", "batch_name", "customer", "male_count", "female_count", "total_weight", "total_price", "male_price", "female_price", "unpaid", "event_id", "created_at"]),
        "feed": (FeedRecordValidator, "feed", ["unique_id", "batch_name", "feed_date", "feed_manufacturer", "feed_item", "sub_location", "is_completed", "feed_week", "feed_additive", "feed_remark", "event_id", "created_at"])
    }
    
    validator_class, table_name, columns = validators[file_type]
    
    valid_records = []
    invalid_count = 0
    
    # 處理每一行資料
    for _, row in df.iterrows():
        try:
            validated_record = validator_class.model_validate(row)
            validated_record.unique_id = hashlib.sha256(
                validated_record.model_dump_json(exclude="unique_id").encode()
            ).hexdigest()[:10]
            
            record_dict = validated_record.model_dump()
            record_dict['created_at'] = datetime.now().isoformat()
            record_dict['event_id'] = event_id  # 加入event_id
            valid_records.append(record_dict)
        except Exception:
            invalid_count += 1
    
    if not valid_records:
        processing_time_ms = int((time.time() - start_time) * 1000)
        log_upload_event(
            event_id=event_id,
            file_name=file.filename or "unknown",
            file_size=file_size,
            file_type=file_type,
            processing_status="failed",
            processing_time_ms=processing_time_ms,
            invalid_count=invalid_count,
            error_message="沒有有效的數據記錄"
        )
        return {
            "success": False,
            "message": "沒有有效的數據記錄",
            "file_type": file_type,
            "valid_count": 0,
            "invalid_count": invalid_count,
            "data": []
        }
    
    # 去重處理
    unique_records = {}
    for record in valid_records:
        unique_id = record.get('unique_id')
        if unique_id:
            unique_records[unique_id] = record
    
    deduplicated_records = list(unique_records.values())
    duplicates_removed = len(valid_records) - len(deduplicated_records)
    
    # 更新資料庫（完整同步：新增不存在的記錄，刪除不在上傳檔案中的記錄）
    conn = get_db_connection()
    try:
        # 獲取現有的 unique_id
        cursor = conn.execute(f"SELECT unique_id FROM {table_name}")
        existing_ids = {row[0] for row in cursor.fetchall()}
        
        # 新增的記錄 unique_id
        upload_ids = {record['unique_id'] for record in deduplicated_records}
        
        # 需要刪除的記錄 (在資料庫中但不在上傳檔案中)
        ids_to_delete = existing_ids - upload_ids
        
        # 需要插入的新記錄 (在上傳檔案中但不在資料庫中)
        ids_to_insert = upload_ids - existing_ids
        
        # 計算重複記錄數量 (兩邊都有的記錄)
        duplicate_count = len(upload_ids & existing_ids)
        
        # 刪除不在上傳檔案中的記錄
        deleted_count = 0
        if ids_to_delete:
            placeholders = ','.join(['?' for _ in ids_to_delete])
            conn.execute(f"DELETE FROM {table_name} WHERE unique_id IN ({placeholders})", list(ids_to_delete))
            deleted_count = len(ids_to_delete)
        
        # 準備插入的資料
        records_to_insert = [r for r in deduplicated_records if r['unique_id'] in ids_to_insert]
        
        # 插入新記錄
        inserted_count = 0
        if records_to_insert:
            placeholders = ", ".join(["?" for _ in columns])
            insert_sql = f"INSERT INTO {table_name} ({', '.join(columns)}) VALUES ({placeholders})"
            
            for record in records_to_insert:
                values = []
                for col in columns:
                    value = record.get(col)
                    if col.endswith('_date') and hasattr(value, 'isoformat'):
                        value = value.isoformat()
                    elif isinstance(value, bool):
                        value = int(value)
                    values.append(value)
                conn.execute(insert_sql, values)
            inserted_count = len(records_to_insert)
        
        conn.commit()
        
        # 組合訊息
        message_parts = []
        if inserted_count > 0:
            message_parts.append(f"新增 {inserted_count} 條記錄")
        if deleted_count > 0:
            message_parts.append(f"刪除 {deleted_count} 條記錄")
        if duplicate_count > 0:
            message_parts.append(f"保持 {duplicate_count} 條已存在記錄")
        if invalid_count > 0:
            message_parts.append(f"跳過 {invalid_count} 條無效記錄")
        if duplicates_removed > 0:
            message_parts.append(f"去重 {duplicates_removed} 條重複記錄")
        
        final_message = f"處理 {file_type} 資料：" + "，".join(message_parts) if message_parts else f"處理 {file_type} 資料完成"
        
        # 記錄成功事件
        processing_time_ms = int((time.time() - start_time) * 1000)
        log_upload_event(
            event_id=event_id,
            file_name=file.filename or "unknown",
            file_size=file_size,
            file_type=file_type,
            processing_status="completed",
            processing_time_ms=processing_time_ms,
            valid_count=len(deduplicated_records),
            invalid_count=invalid_count,
            duplicates_removed=duplicates_removed,
            inserted_count=inserted_count,
            deleted_count=deleted_count,
            duplicate_count=duplicate_count,
            metadata={
                "total_rows": len(df),
                "columns": list(df.columns),
                "table_name": table_name
            }
        )
        
        return {
            "success": True,
            "message": final_message,
            "file_type": file_type,
            "valid_count": len(deduplicated_records),
            "invalid_count": invalid_count,
            "duplicates_removed": duplicates_removed,
            "inserted_count": inserted_count,
            "deleted_count": deleted_count,
            "duplicate_count": duplicate_count,
            "event_id": event_id,
            "processing_time_ms": processing_time_ms,
            "data": deduplicated_records[:50]  # 只返回前50筆
        }
        
    except Exception as e:
        logger.error(f"資料庫操作失敗: {e}")
        processing_time_ms = int((time.time() - start_time) * 1000)
        log_upload_event(
            event_id=event_id,
            file_name=file.filename or "unknown",
            file_size=file_size,
            file_type=file_type,
            processing_status="error",
            processing_time_ms=processing_time_ms,
            valid_count=len(valid_records) if 'valid_records' in locals() else 0,
            invalid_count=invalid_count,
            error_message=f"資料庫操作失敗: {str(e)}"
        )
        return {
            "success": False,
            "message": f"資料庫操作失敗: {str(e)}",
            "file_type": file_type,
            "valid_count": 0,
            "invalid_count": invalid_count,
            "data": []
        }
    finally:
        conn.close()

@app.post("/upload/breeds")
async def upload_breeds(file: UploadFile):
    """Web表單上傳路由，支援三種類型檔案"""
    result = await process_upload(file)
    
    if result["success"]:
        # 根據檔案類型獲取對應資料
        if result["file_type"] == "breed":
            data = get_all_breeds()
        elif result["file_type"] == "sale":
            conn = get_db_connection()
            try:
                cursor = conn.execute("SELECT * FROM sale ORDER BY sale_date DESC")
                data = cursor.fetchall()
            finally:
                conn.close()
        elif result["file_type"] == "feed":
            conn = get_db_connection()
            try:
                cursor = conn.execute("SELECT * FROM feed ORDER BY feed_date DESC")
                data = cursor.fetchall()
            finally:
                conn.close()
        else:
            data = []
        
        data_list = [dict(row) for row in data]
        table_result = render_table(pd.DataFrame(data_list), page=0)
        
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
    return await process_upload(file)

@rt('/')
def index():
    # breeds = get_all_breeds()
    # breed_data = [dict(breed) for breed in breeds]
    return Titled("Cleansales", 
        upload_breeds_form,
        Hr(),
        sql_query_form,
        Hr(),
        Div(
            A("查看上傳歷史", href="/events", style="background: #007bff; color: white; padding: 8px 16px; text-decoration: none; border-radius: 4px; display: inline-block; margin-bottom: 10px;"),
            style="margin-bottom: 15px;"
        ),
        Div(Span('載入中...', id="loading", cls='htmx-indicator' ), hx_get="/q", hx_target="#result", hx_trigger='load', hx_indicator="#loading"),
        Div(id="result"))

@rt('/b')
def sql_breeds():
    """顯示批次統計資料，包含到期日計算"""
    conn = get_db_connection()
    try:
        cursor = conn.execute("""
            SELECT 
                batch_name,
                chicken_breed,
                SUM(breed_male) AS male,
                SUM(breed_female) AS female,
                MIN(breed_date) AS breed_date,
                DATE(breed_date, '+120 days') AS expire_date,
                COUNT(batch_name) AS count
            FROM breed 
            WHERE is_completed = 0 
            GROUP BY batch_name 
            ORDER BY expire_date DESC
        """)
        results = cursor.fetchall()
        data = [dict(breed) for breed in results]
        return render_table(pd.DataFrame(data), current_column="expire_date", current_order="DESC")
    finally:
        conn.close()
@rt('/q')
def query_breed(column: str | None = None, order: str | None = None):
    conn = get_db_connection()
    try:
        if column:
            cursor = conn.execute("""
                SELECT *
                FROM breed 
                ORDER BY {column} {order}
            """.format(column=column, order=order or "DESC"))
        else:
            cursor = conn.execute("SELECT * FROM breed ORDER BY breed_date DESC")
        
        results = cursor.fetchall()
        data = [dict(breed) for breed in results]
        return render_table(pd.DataFrame(data), current_column=column, current_order=order or "DESC", page=0)
    finally:
        conn.close()

@rt('/load_more')
def load_more_data(column: str = "", order: str = "DESC", page: int = 1):
    conn = get_db_connection()
    try:
        if column:
            cursor = conn.execute("""
                SELECT *
                FROM breed 
                ORDER BY {column} {order}
            """.format(column=column, order=order))
        else:
            cursor = conn.execute("SELECT * FROM breed ORDER BY breed_date DESC")
        
        results = cursor.fetchall()
        data = [dict(breed) for breed in results]
        return render_table(pd.DataFrame(data), current_column=column, current_order=order, page=page)
    finally:
        conn.close()

@rt('/events')
def view_upload_events():
    """查看上傳事件歷史"""
    conn = get_db_connection()
    try:
        cursor = conn.execute("""
            SELECT 
                event_id,
                file_type,
                file_name,
                file_size,
                upload_timestamp,
                processing_status,
                valid_count,
                invalid_count,
                duplicates_removed,
                inserted_count,
                deleted_count,
                duplicate_count,
                error_message,
                processing_time_ms
            FROM upload_events 
            ORDER BY upload_timestamp DESC
            LIMIT 100
        """)
        results = cursor.fetchall()
        
        if not results:
            return Div("目前沒有上傳記錄")
        
        data = [dict(row) for row in results]
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
            render_table(df, current_column="upload_timestamp", current_order="DESC", page=0, enable_event_links=True),
            style="margin: 20px 0;"
        )
    except Exception as e:
        return Div(f"查詢上傳事件失敗: {str(e)}", style="color: red;")
    finally:
        conn.close()

@rt('/event/{event_id}')
def view_event_records(event_id: str):
    """查看特定事件的數據記錄"""
    conn = get_db_connection()
    try:
        # 首先獲取事件信息
        event_cursor = conn.execute("""
            SELECT file_type, file_name, upload_timestamp, processing_status,
                   inserted_count, deleted_count, duplicate_count
            FROM upload_events 
            WHERE event_id = ?
        """, (event_id,))
        event_info = event_cursor.fetchone()
        
        if not event_info:
            return Div(
                H2("事件記錄"),
                P(f"找不到事件 ID: {event_id}", style="color: red;"),
                A("返回事件列表", href="/events", style="color: #007bff;")
            )
        
        event_dict = dict(event_info)
        file_type = event_dict['file_type']
        
        # 根據文件類型查詢對應的數據表
        table_map = {
            'breed': 'breed',
            'sale': 'sale', 
            'feed': 'feed'
        }
        
        if file_type not in table_map:
            return Div(
                H2("事件記錄"),
                P(f"不支持的文件類型: {file_type}", style="color: red;"),
                A("返回事件列表", href="/events", style="color: #007bff;")
            )
        
        table_name = table_map[file_type]
        
        # 查詢該事件的所有記錄
        data_cursor = conn.execute(f"""
            SELECT * FROM {table_name} 
            WHERE event_id = ?
            ORDER BY created_at DESC
        """, (event_id,))
        data_records = data_cursor.fetchall()
        
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
            A("返回事件列表", href="/events", style="color: #007bff; margin-bottom: 15px; display: inline-block;")
        ]
        
        if data_records:
            data_list = [dict(row) for row in data_records]
            df = pd.DataFrame(data_list)
            
            # 移除event_id欄位以避免重複顯示
            if 'event_id' in df.columns:
                df = df.drop('event_id', axis=1)
            
            content.extend([
                H3(f"數據記錄 ({len(data_records)} 條)"),
                render_table(df, page=0)
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
    finally:
        conn.close()

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
    
    conn = get_db_connection()
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
            render_table(df)
        )
        
    except Exception as e:
        return Div(f"SQL執行錯誤: {str(e)}", style="color: red;")
    finally:
        conn.close()

def main():
    serve()


if __name__ == "__main__":
    main()