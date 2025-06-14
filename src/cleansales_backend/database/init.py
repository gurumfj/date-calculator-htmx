import logging
import sqlite3

logger = logging.getLogger(__name__)


def init_db(db_path: str = "./data/sqlite.db"):
    """初始化數據庫表"""
    conn = sqlite3.connect(db_path)
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
        """)
        conn.commit()
    except Exception as e:
        logger.error("創建數據表失敗: %s", str(e))
    finally:
        conn.close()