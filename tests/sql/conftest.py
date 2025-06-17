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
            id INTEGER PRIMARY KEY,
            batch_name TEXT NOT NULL,
            chicken_breed TEXT NOT NULL,
            breed_date DATE NOT NULL,
            breed_male INTEGER DEFAULT 0,
            breed_female INTEGER DEFAULT 0
        );
        
        CREATE TABLE sale (
            id INTEGER PRIMARY KEY,
            batch_name TEXT NOT NULL,
            sale_date DATE NOT NULL,
            male_count INTEGER DEFAULT 0,
            female_count INTEGER DEFAULT 0,
            customer TEXT,
            total_price REAL,
            total_weight REAL,
            male_price REAL,
            female_price REAL
        );
        
        CREATE TABLE farm_production (
            id INTEGER PRIMARY KEY,
            batch_name TEXT NOT NULL,
            fcr REAL
        );
        
        CREATE TABLE feed (
            id INTEGER PRIMARY KEY,
            batch_name TEXT NOT NULL,
            feed_manufacturer TEXT
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
        INSERT INTO breed (batch_name, chicken_breed, breed_date, breed_male, breed_female)
        VALUES (?, ?, ?, ?, ?)
    """, [
        ('古早001', '古早', '2024-01-01', 100, 120),
        ('古早002', '古早', '2024-01-15', 80, 90),
        ('閹雞001', '閹雞', '2024-02-01', 50, 60),
        ('測試批次', '古早', '2024-03-01', 150, 180),
    ])
    
    # 插入測試銷售數據
    conn.executemany("""
        INSERT INTO sale (batch_name, sale_date, male_count, female_count, customer, total_price, total_weight, male_price, female_price)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, [
        ('古早001', '2024-03-01', 20, 25, '客戶A', 9000.0, 60.0, 200.0, 180.0),
        ('古早001', '2024-03-15', 15, 20, '客戶B', 7000.0, 45.0, 200.0, 180.0),
        ('古早002', '2024-03-10', 10, 15, '客戶A', 5000.0, 32.0, 200.0, 180.0),
        ('測試批次', '2024-05-01', 30, 40, '客戶C', 14000.0, 90.0, 200.0, 180.0),
    ])
    
    # 插入測試FCR數據
    conn.executemany("""
        INSERT INTO farm_production (batch_name, fcr)
        VALUES (?, ?)
    """, [
        ('古早001', 1.85),
        ('古早002', 1.92),
        ('閹雞001', 2.1),
    ])
    
    # 插入測試飼料數據
    conn.executemany("""
        INSERT INTO feed (batch_name, feed_manufacturer)
        VALUES (?, ?)
    """, [
        ('古早001', '大成飼料'),
        ('古早002', '福壽飼料'),
        ('古早001', '卜蜂飼料'),  # 同一批次多種飼料
    ])
    
    conn.commit()
    return conn