"""
################################################################################
# 數據庫優化模組
#
# 這個模組提供了SQLite數據庫的優化配置，包括：
# 1. WAL模式啟用
# 2. 索引創建
# 3. 緩存配置
################################################################################
"""

import logging
from sqlalchemy import event, text
from sqlmodel import Session

logger = logging.getLogger(__name__)

def optimize_sqlite_connection(dbapi_connection, connection_record):
    """優化SQLite連接配置"""
    cursor = dbapi_connection.cursor()
    
    # 啟用WAL模式
    cursor.execute("PRAGMA journal_mode=WAL")
    
    # 設置頁面緩存大小（默認-2000表示2000KB）
    cursor.execute("PRAGMA page_size=4096")
    cursor.execute("PRAGMA cache_size=-2000")
    
    # 啟用外鍵約束
    cursor.execute("PRAGMA foreign_keys=ON")
    
    # 同步模式設置（0=OFF, 1=NORMAL, 2=FULL, 3=EXTRA）
    cursor.execute("PRAGMA synchronous=NORMAL")
    
    # 設置mmap大小（單位：字節）
    cursor.execute("PRAGMA mmap_size=30000000000")
    
    # 設置臨時存儲位置
    cursor.execute("PRAGMA temp_store=MEMORY")
    
    cursor.close()

def create_indexes(session: Session):
    """創建必要的索引"""
    try:
        # 為breed_records表創建索引
        session.exec(
            text("""
                CREATE INDEX IF NOT EXISTS idx_breed_batch_name 
                ON breedrecordorm (batch_name);
            """)
        )
        
        # 為sale_records表創建索引
        session.exec(
            text("""
                CREATE INDEX IF NOT EXISTS idx_sale_location 
                ON salerecordorm (location);
            """)
        )
        
        session.commit()
        logger.info("成功創建數據庫索引")
    except Exception as e:
        logger.error(f"創建索引時發生錯誤: {e}")
        session.rollback()
        raise

def setup_db_optimizations(engine):
    """設置數據庫優化"""
    # 註冊連接事件監聽器
    event.listen(engine, 'connect', optimize_sqlite_connection)
    
    # 創建索引
    with Session(engine) as session:
        create_indexes(session)
