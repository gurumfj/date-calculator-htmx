from datetime import datetime


class TestBatchSummarySQL:
    """測試 batch_summary.sql 查詢"""
    
    def test_batch_summary_basic_query(self, sample_data, sql_templates):
        """測試基本批次摘要查詢"""
        conn = sample_data
        
        # 渲染SQL模板
        sql_query = sql_templates.get_template("batch_summary.sql").render(
            limit=False, 
            batch_name=None
        )
        
        # 執行查詢
        cursor = conn.cursor()
        cursor.execute(sql_query, {"chicken_breed": "古早"})
        results = cursor.fetchall()
        
        # 驗證結果
        assert len(results) == 3  # 古早001, 古早002, 測試批次
        
        # 驗證第一筆資料結構
        first_result = results[0]
        assert "idx" in first_result.keys()
        assert "batch_name" in first_result.keys()
        assert "chicken_breed" in first_result.keys()
        assert "breed_date" in first_result.keys()
        assert "dayage" in first_result.keys()
        assert "week_age" in first_result.keys()
        assert "total_b_male" in first_result.keys()
        assert "total_b_female" in first_result.keys()
        assert "total_count" in first_result.keys()
        assert "percentage" in first_result.keys()
        assert "fcr" in first_result.keys()
        assert "expire_date" in first_result.keys()
    
    def test_batch_summary_with_search(self, sample_data, sql_templates):
        """測試帶搜尋條件的批次摘要查詢"""
        conn = sample_data
        
        # 渲染SQL模板（搜尋測試批次）
        sql_query = sql_templates.get_template("batch_summary.sql").render(
            limit=False,
            batch_name=True
        )
        
        # 執行查詢
        cursor = conn.cursor()
        cursor.execute(sql_query, {
            "chicken_breed": "古早",
            "batch_name": "%測試%"
        })
        results = cursor.fetchall()
        
        # 驗證結果
        assert len(results) == 1
        assert results[0]["batch_name"] == "測試批次"
    
    def test_batch_summary_with_limit(self, sample_data, sql_templates):
        """測試帶分頁的批次摘要查詢"""
        conn = sample_data
        
        # 渲染SQL模板
        sql_query = sql_templates.get_template("batch_summary.sql").render(
            limit=True,
            batch_name=None
        )
        
        # 執行查詢
        cursor = conn.cursor()
        cursor.execute(sql_query, {
            "chicken_breed": "古早",
            "limit": 2,
            "offset": 0
        })
        results = cursor.fetchall()
        
        # 驗證結果
        assert len(results) == 2
    
    def test_batch_summary_calculations(self, sample_data, sql_templates):
        """測試批次摘要的計算邏輯"""
        conn = sample_data
        
        # 渲染SQL模板
        sql_query = sql_templates.get_template("batch_summary.sql").render(
            limit=False,
            batch_name=True
        )
        
        # 執行查詢（古早001）
        cursor = conn.cursor()
        cursor.execute(sql_query, {
            "chicken_breed": "古早",
            "batch_name": "%古早001%"
        })
        result = cursor.fetchone()
        
        # 驗證計算結果
        assert result["batch_name"] == "古早001"
        assert result["total_b_male"] == 100
        assert result["total_b_female"] == 120
        # 驗證銷售總數（實際值需要根據數據計算）
        assert result["total_count"] >= 0
        
        # 驗證銷售率計算
        total_breed = result["total_b_male"] + result["total_b_female"]  # 220
        expected_percentage = (result["total_count"] * 100.0) / total_breed
        assert abs(result["percentage"] - expected_percentage) < 0.01
        
        # 驗證FCR
        assert result["fcr"] == 1.85
        
        # 驗證週齡計算格式
        assert "/" in result["week_age"]
    
    def test_batch_summary_week_age_calculation(self, sample_data, sql_templates):
        """測試週齡計算邏輯"""
        conn = sample_data
        
        # 創建特定日期的測試數據來驗證週齡計算
        conn.execute("""
            INSERT INTO breed (batch_name, chicken_breed, breed_date, breed_male, breed_female)
            VALUES ('週齡測試', '古早', date('now', '-14 days'), 100, 100)
        """)
        conn.commit()
        
        # 渲染SQL模板
        sql_query = sql_templates.get_template("batch_summary.sql").render(
            limit=False,
            batch_name=True
        )
        
        # 執行查詢
        cursor = conn.cursor()
        cursor.execute(sql_query, {
            "chicken_breed": "古早",
            "batch_name": "%週齡測試%"
        })
        result = cursor.fetchone()
        
        # 驗證週齡格式
        week_age = result["week_age"]
        assert "/" in week_age
        parts = week_age.split("/")
        assert len(parts) == 2
        assert parts[0].isdigit()  # 週數
        assert parts[1].isdigit()  # 天數或7
    
    def test_batch_summary_feed_concatenation(self, sample_data, sql_templates):
        """測試飼料名稱串接"""
        conn = sample_data
        
        # 渲染SQL模板
        sql_query = sql_templates.get_template("batch_summary.sql").render(
            limit=False,
            batch_name=True
        )
        
        # 執行查詢（古早001有多種飼料）
        cursor = conn.cursor()
        cursor.execute(sql_query, {
            "chicken_breed": "古早",
            "batch_name": "%古早001%"
        })
        result = cursor.fetchone()
        
        # 驗證飼料串接
        feed = result["feed"]
        assert "大成飼料" in feed
        assert "卜蜂飼料" in feed
        assert "," in feed  # GROUP_CONCAT 的分隔符
    
    def test_batch_summary_expire_date_calculation(self, sample_data, sql_templates):
        """測試到期日計算"""
        conn = sample_data
        
        # 渲染SQL模板
        sql_query = sql_templates.get_template("batch_summary.sql").render(
            limit=False,
            batch_name=None
        )
        
        # 執行查詢
        cursor = conn.cursor()
        cursor.execute(sql_query, {"chicken_breed": "古早"})
        results = cursor.fetchall()
        
        for result in results:
            breed_date = datetime.strptime(result["breed_date"], "%Y-%m-%d").date()
            expire_date = datetime.strptime(result["expire_date"], "%Y-%m-%d").date()
            
            # 古早雞種應該是119天
            if result["chicken_breed"] == "古早":
                expected_days = 119
            elif result["chicken_breed"] == "閹雞":
                expected_days = 175
            else:
                continue
                
            actual_days = (expire_date - breed_date).days
            assert actual_days == expected_days
    
    def test_batch_summary_no_results(self, sample_data, sql_templates):
        """測試無結果的查詢"""
        conn = sample_data
        
        # 渲染SQL模板
        sql_query = sql_templates.get_template("batch_summary.sql").render(
            limit=False,
            batch_name=None
        )
        
        # 執行查詢（不存在的雞種）
        cursor = conn.cursor()
        cursor.execute(sql_query, {"chicken_breed": "不存在的雞種"})
        results = cursor.fetchall()
        
        # 驗證結果
        assert len(results) == 0
    
    def test_batch_summary_order_by_expire_date(self, sample_data, sql_templates):
        """測試結果按到期日排序"""
        conn = sample_data
        
        # 渲染SQL模板
        sql_query = sql_templates.get_template("batch_summary.sql").render(
            limit=False,
            batch_name=None
        )
        
        # 執行查詢
        cursor = conn.cursor()
        cursor.execute(sql_query, {"chicken_breed": "古早"})
        results = cursor.fetchall()
        
        # 驗證排序（應該按到期日降序排列）
        if len(results) > 1:
            for i in range(len(results) - 1):
                current_expire = datetime.strptime(results[i]["expire_date"], "%Y-%m-%d").date()
                next_expire = datetime.strptime(results[i + 1]["expire_date"], "%Y-%m-%d").date()
                assert current_expire >= next_expire