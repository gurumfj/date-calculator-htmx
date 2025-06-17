class TestCountDataQuerySQL:
    """測試 count_data_query.sql 查詢"""
    
    def test_count_data_query_basic(self, sample_data, sql_templates):
        """測試基本計數查詢"""
        conn = sample_data
        
        # 渲染SQL模板
        sql_query = sql_templates.get_template("count_data_query.sql").render(
            table_name="breed",
            event_id=False
        )
        
        # 執行查詢
        cursor = conn.cursor()
        cursor.execute(sql_query)
        result = cursor.fetchone()
        
        # 驗證結果
        assert result[0] == 4  # 應該有4筆breed記錄
    
    def test_count_data_query_with_event_id(self, test_db, sql_templates):
        """測試帶event_id條件的計數查詢"""
        conn, _ = test_db
        
        # 創建帶event_id的測試表
        conn.execute("""
            CREATE TABLE test_events (
                id INTEGER PRIMARY KEY,
                event_id INTEGER,
                data TEXT
            )
        """)
        
        # 插入測試數據
        conn.executemany("""
            INSERT INTO test_events (event_id, data) VALUES (?, ?)
        """, [
            (1, 'event1_data1'),
            (1, 'event1_data2'),
            (2, 'event2_data1'),
            (3, 'event3_data1'),
        ])
        conn.commit()
        
        # 渲染SQL模板
        sql_query = sql_templates.get_template("count_data_query.sql").render(
            table_name="test_events",
            event_id=True
        )
        
        # 執行查詢（計算event_id=1的記錄數）
        cursor = conn.cursor()
        cursor.execute(sql_query, {"event_id": 1})
        result = cursor.fetchone()
        
        # 驗證結果
        assert result[0] == 2  # event_id=1有2筆記錄
    
    def test_count_data_query_different_tables(self, sample_data, sql_templates):
        """測試不同表的計數查詢"""
        conn = sample_data
        
        # 測試breed表
        sql_query = sql_templates.get_template("count_data_query.sql").render(
            table_name="breed",
            event_id=False
        )
        cursor = conn.cursor()
        cursor.execute(sql_query)
        breed_count = cursor.fetchone()[0]
        
        # 測試sale表
        sql_query = sql_templates.get_template("count_data_query.sql").render(
            table_name="sale",
            event_id=False
        )
        cursor.execute(sql_query)
        sale_count = cursor.fetchone()[0]
        
        # 驗證結果
        assert breed_count == 4
        assert sale_count == 4
    
    def test_count_data_query_empty_result(self, test_db, sql_templates):
        """測試空結果的計數查詢"""
        conn, _ = test_db
        
        # 創建空表
        conn.execute("""
            CREATE TABLE empty_table (
                id INTEGER PRIMARY KEY,
                event_id INTEGER
            )
        """)
        
        # 渲染SQL模板
        sql_query = sql_templates.get_template("count_data_query.sql").render(
            table_name="empty_table",
            event_id=False
        )
        
        # 執行查詢
        cursor = conn.cursor()
        cursor.execute(sql_query)
        result = cursor.fetchone()
        
        # 驗證結果
        assert result[0] == 0