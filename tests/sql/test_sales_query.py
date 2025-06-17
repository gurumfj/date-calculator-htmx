import pytest


class TestSalesQuerySQL:
    """測試 sales_query.sql 查詢"""
    
    @pytest.fixture
    def sales_test_data(self, sample_data):
        """使用已有的銷售測試數據"""
        return sample_data
    
    def test_sales_query_basic(self, sales_test_data, sql_templates):
        """測試基本銷售查詢"""
        conn = sales_test_data
        
        # 渲染SQL模板
        sql_query = sql_templates.get_template("sales_query.sql").render(search=False)
        
        # 執行查詢
        cursor = conn.cursor()
        cursor.execute(sql_query, {"limit": 10, "offset": 0})
        results = cursor.fetchall()
        
        # 驗證結果
        assert len(results) == 4
        
        # 驗證欄位存在
        first_result = results[0]
        assert "sale_date" in first_result.keys()
        assert "batch_name" in first_result.keys()
        assert "customer" in first_result.keys()
        assert "male_count" in first_result.keys()
        assert "female_count" in first_result.keys()
        assert "avg_price" in first_result.keys()
        assert "male_avg_weight" in first_result.keys()
        assert "female_avg_weight" in first_result.keys()
        assert "male_price" in first_result.keys()
        assert "female_price" in first_result.keys()
    
    def test_sales_query_with_search(self, sales_test_data, sql_templates):
        """測試帶搜尋條件的銷售查詢"""
        conn = sales_test_data
        
        # 渲染SQL模板（搜尋客戶A）
        sql_query = sql_templates.get_template("sales_query.sql").render(search=True)
        
        # 執行查詢
        cursor = conn.cursor()
        cursor.execute(sql_query, {
            "search": "%客戶A%",
            "limit": 10,
            "offset": 0
        })
        results = cursor.fetchall()
        
        # 驗證結果
        assert len(results) == 2  # 應該找到2筆客戶A的記錄
        for result in results:
            assert result["customer"] == "客戶A"
    
    def test_sales_query_batch_search(self, sales_test_data, sql_templates):
        """測試批次名稱搜尋"""
        conn = sales_test_data
        
        # 渲染SQL模板（搜尋測試批次）
        sql_query = sql_templates.get_template("sales_query.sql").render(search=True)
        
        # 執行查詢
        cursor = conn.cursor()
        cursor.execute(sql_query, {
            "search": "%測試%",
            "limit": 10,
            "offset": 0
        })
        results = cursor.fetchall()
        
        # 驗證結果
        assert len(results) == 1
        assert results[0]["batch_name"] == "測試批次"
    
    def test_sales_query_avg_price_calculation(self, sales_test_data, sql_templates):
        """測試平均價格計算"""
        conn = sales_test_data
        
        # 渲染SQL模板
        sql_query = sql_templates.get_template("sales_query.sql").render(search=False)
        
        # 執行查詢
        cursor = conn.cursor()
        cursor.execute(sql_query, {"limit": 10, "offset": 0})
        results = cursor.fetchall()
        
        # 驗證平均價格計算
        for result in results:
            if "total_price" in result.keys() and result["avg_price"] is not None:
                total_count = result["male_count"] + result["female_count"]
                if total_count > 0:
                    expected_avg = result["total_price"] / total_count
                    assert abs(result["avg_price"] - expected_avg) < 0.01
    
    def test_sales_query_weight_calculation(self, sales_test_data, sql_templates):
        """測試重量計算"""
        conn = sales_test_data
        
        # 渲染SQL模板
        sql_query = sql_templates.get_template("sales_query.sql").render(search=False)
        
        # 執行查詢
        cursor = conn.cursor()
        cursor.execute(sql_query, {"limit": 10, "offset": 0})
        results = cursor.fetchall()
        
        # 驗證重量計算邏輯
        for result in results:
            if ("total_weight" in result.keys() and 
                result["male_avg_weight"] is not None and
                result["male_count"] > 0 and 
                result["female_count"] > 0):
                
                male_count = result["male_count"]
                female_count = result["female_count"]
                total_weight = result["total_weight"]
                
                # 驗證公重計算
                expected_male_avg = ((total_weight - male_count * 0.8) / (male_count + female_count)) + 0.8
                if result["male_avg_weight"] is not None:
                    assert abs(result["male_avg_weight"] - expected_male_avg) < 0.01
                
                # 驗證母重計算
                expected_female_avg = (total_weight - male_count * 0.8) / (male_count + female_count)
                if result["female_avg_weight"] is not None:
                    assert abs(result["female_avg_weight"] - expected_female_avg) < 0.01
    
    def test_sales_query_order_by_date_desc(self, sales_test_data, sql_templates):
        """測試按日期降序排列"""
        conn = sales_test_data
        
        # 渲染SQL模板
        sql_query = sql_templates.get_template("sales_query.sql").render(search=False)
        
        # 執行查詢
        cursor = conn.cursor()
        cursor.execute(sql_query, {"limit": 10, "offset": 0})
        results = cursor.fetchall()
        
        # 驗證排序
        if len(results) > 1:
            for i in range(len(results) - 1):
                current_date = results[i]["sale_date"]
                next_date = results[i + 1]["sale_date"]
                assert current_date >= next_date
    
    def test_sales_query_pagination(self, sales_test_data, sql_templates):
        """測試分頁功能"""
        conn = sales_test_data
        
        # 渲染SQL模板
        sql_query = sql_templates.get_template("sales_query.sql").render(search=False)
        
        # 測試第一頁
        cursor = conn.cursor()
        cursor.execute(sql_query, {"limit": 2, "offset": 0})
        page1_results = cursor.fetchall()
        assert len(page1_results) == 2
        
        # 測試第二頁
        cursor.execute(sql_query, {"limit": 2, "offset": 2})
        page2_results = cursor.fetchall()
        assert len(page2_results) == 2
        
        # 驗證不同頁面的記錄不重複
        page1_dates = [r["sale_date"] for r in page1_results]
        page2_dates = [r["sale_date"] for r in page2_results]
        assert len(set(page1_dates) & set(page2_dates)) == 0  # 沒有交集
    
    def test_sales_query_null_handling(self, sales_test_data, sql_templates):
        """測試NULL值處理"""
        conn = sales_test_data
        
        # 插入NULL值測試數據
        conn.execute("""
            INSERT INTO sale (sale_date, batch_name, customer, male_count, female_count, 
                            total_price, total_weight, male_price, female_price)
            VALUES ('2024-06-01', 'NULL測試', '客戶D', 0, 0, NULL, NULL, NULL, NULL)
        """)
        conn.commit()
        
        # 渲染SQL模板
        sql_query = sql_templates.get_template("sales_query.sql").render(search=False)
        
        # 執行查詢
        cursor = conn.cursor()
        cursor.execute(sql_query, {"limit": 10, "offset": 0})
        results = cursor.fetchall()
        
        # 找到NULL測試記錄
        null_test_record = None
        for result in results:
            if result["batch_name"] == "NULL測試":
                null_test_record = result
                break
        
        assert null_test_record is not None
        assert null_test_record["avg_price"] is None
        assert null_test_record["male_avg_weight"] is None
        assert null_test_record["female_avg_weight"] is None