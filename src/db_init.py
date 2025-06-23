"""
Database initialization and management utilities.
"""

import logging
import sqlite3
from contextlib import contextmanager

logger = logging.getLogger(__name__)

DEFAULT_DB_PATH = "./data/sqlite.db"


def _setup_connection_pragmas(conn: sqlite3.Connection):
    """
    統一設置資料庫連接的 PRAGMA 參數
    
    Args:
        conn: 資料庫連接對象
    """
    conn.row_factory = sqlite3.Row  # 啟用字典式訪問
    
    # 統一設置 WAL 模式和優化參數
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    conn.execute("PRAGMA temp_store=MEMORY")


def get_db_connection(db_path: str = DEFAULT_DB_PATH) -> sqlite3.Connection:
    """
    獲取數據庫連接，統一使用 WAL 模式
    
    Args:
        db_path: 數據庫文件路徑，默認為 "./data/sqlite.db"
        
    Returns:
        sqlite3.Connection: 數據庫連接對象，已設置 row_factory 和 WAL 模式
        
    Raises:
        sqlite3.Error: 數據庫連接失敗時拋出異常
    """
    try:
        conn = sqlite3.connect(db_path)
        _setup_connection_pragmas(conn)
        logger.debug(f"成功連接到數據庫: {db_path}")
        return conn
    except sqlite3.Error as e:
        logger.error(f"數據庫連接失敗: {db_path}, 錯誤: {e}")
        raise


@contextmanager
def get_db_connection_context(db_path: str = DEFAULT_DB_PATH):
    """
    安全的數據庫連接上下文管理器，統一使用 WAL 模式
    
    Args:
        db_path: 數據庫文件路徑
        
    Yields:
        sqlite3.Connection: 數據庫連接對象
    """
    conn = sqlite3.connect(db_path)
    try:
        _setup_connection_pragmas(conn)
        yield conn
        conn.commit()  # 確保事務被提交
    except Exception as e:
        conn.rollback()  # 發生錯誤時回滾
        logger.error(f"數據庫操作失敗: {e}")
        raise
    finally:
        conn.close()



def init_db(db_path: str = DEFAULT_DB_PATH):
    """初始化數據庫表"""
    conn = get_db_connection(db_path)
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
            
            CREATE TABLE IF NOT EXISTS farm_production (
                unique_id TEXT PRIMARY KEY,
                batch_name TEXT NOT NULL,
                farm_location TEXT,
                farmer TEXT,
                chick_in_count INTEGER,
                chicken_out_count INTEGER,
                feed_weight REAL,
                sale_weight_jin REAL,
                fcr REAL,
                meat_cost REAL,
                avg_price REAL,
                cost_price REAL,
                revenue REAL,
                expenses REAL,
                feed_cost REAL,
                vet_cost REAL,
                feed_med_cost REAL,
                farm_med_cost REAL,
                leg_band_cost REAL,
                chick_cost REAL,
                grow_fee REAL,
                catch_fee REAL,
                weigh_fee REAL,
                gas_cost REAL,
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
            
            CREATE TABLE IF NOT EXISTS todoist_cache (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                batch_name TEXT NOT NULL,
                task_id TEXT NOT NULL,
                task_type TEXT NOT NULL,
                content TEXT,
                description TEXT,
                due_date TEXT,
                completed_at TEXT,
                labels TEXT,
                priority INTEGER,
                created_at TEXT,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                cached_at TEXT DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(batch_name, task_id, task_type)
            );
            
            CREATE INDEX IF NOT EXISTS idx_todoist_cache_batch_name 
            ON todoist_cache(batch_name);
            
            CREATE INDEX IF NOT EXISTS idx_todoist_cache_cached_at 
            ON todoist_cache(cached_at);
            
            CREATE INDEX IF NOT EXISTS idx_todoist_cache_batch_task_type 
            ON todoist_cache(batch_name, task_type);
            
            CREATE TABLE IF NOT EXISTS todoist_cache_metadata (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                batch_name TEXT NOT NULL,
                task_type TEXT NOT NULL,
                query_timestamp TEXT NOT NULL,
                task_count INTEGER DEFAULT 0,
                UNIQUE(batch_name, task_type)
            );
            
            CREATE INDEX IF NOT EXISTS idx_cache_metadata_batch_type 
            ON todoist_cache_metadata(batch_name, task_type);
        """)
        conn.commit()
    except Exception as e:
        logger.error("創建數據表失敗: %s", str(e))
    finally:
        conn.close()