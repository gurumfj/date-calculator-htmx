import sqlite3
import tempfile
from pathlib import Path

import pytest
from fastapi.templating import Jinja2Templates


@pytest.fixture
def test_db():
    """創建測試用的SQLite資料庫"""
    # 創建臨時資料庫
    db_fd, db_path = tempfile.mkstemp(suffix='.db')
    import os
    os.close(db_fd)  # 關閉文件描述符
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    
    # 創建測試表格
    conn.executescript("""
        CREATE TABLE breed (
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
        
        CREATE TABLE sale (
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
        
        CREATE TABLE farm_production (
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
        
        CREATE TABLE feed (
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
    """)
    
    yield conn, db_path
    
    # 清理
    conn.close()
    Path(db_path).unlink()


@pytest.fixture
def sql_templates():
    """SQL模板引擎"""
    return Jinja2Templates(directory="src/server/templates/sql")


@pytest.fixture
def sample_data(test_db):
    """插入測試數據"""
    conn, _ = test_db
    
    # 插入測試繁殖數據
    conn.executemany("""
        INSERT INTO breed (unique_id, farm_name, batch_name, chicken_breed, breed_date, breed_male, breed_female, supplier)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, [
        ('breed_001', '測試農場A', '古早001', '古早', '2024-01-01', 100, 120, '供應商A'),
        ('breed_002', '測試農場A', '古早002', '古早', '2024-01-15', 80, 90, '供應商B'),
        ('breed_003', '測試農場B', '閹雞001', '閹雞', '2024-02-01', 50, 60, '供應商A'),
        ('breed_004', '測試農場A', '測試批次', '古早', '2024-03-01', 150, 180, '供應商C'),
    ])
    
    # 插入測試銷售數據
    conn.executemany("""
        INSERT INTO sale (unique_id, batch_name, sale_date, male_count, female_count, customer, total_price, total_weight, male_price, female_price)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, [
        ('sale_001', '古早001', '2024-03-01', 20, 25, '客戶A', 9000.0, 60.0, 200.0, 180.0),
        ('sale_002', '古早001', '2024-03-15', 15, 20, '客戶B', 7000.0, 45.0, 200.0, 180.0),
        ('sale_003', '古早002', '2024-03-10', 10, 15, '客戶A', 5000.0, 32.0, 200.0, 180.0),
        ('sale_004', '測試批次', '2024-05-01', 30, 40, '客戶C', 14000.0, 90.0, 200.0, 180.0),
    ])
    
    # 插入測試FCR數據
    conn.executemany("""
        INSERT INTO farm_production (unique_id, batch_name, fcr)
        VALUES (?, ?, ?)
    """, [
        ('prod_001', '古早001', 1.85),
        ('prod_002', '古早002', 1.92),
        ('prod_003', '閹雞001', 2.1),
    ])
    
    # 插入測試飼料數據
    conn.executemany("""
        INSERT INTO feed (unique_id, batch_name, feed_date, feed_manufacturer, feed_item)
        VALUES (?, ?, ?, ?, ?)
    """, [
        ('feed_001', '古早001', '2024-01-05', '大成飼料', 'starter'),
        ('feed_002', '古早002', '2024-01-20', '福壽飼料', 'grower'),
        ('feed_003', '古早001', '2024-01-20', '卜蜂飼料', 'finisher'),  # 同一批次多種飼料
    ])
    
    conn.commit()
    return conn