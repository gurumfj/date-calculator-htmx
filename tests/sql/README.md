# SQL 查詢測試

這個目錄包含對 `src/server/templates/sql/` 中 SQL 查詢模板的 pytest 測試。

## 測試覆蓋範圍

### 1. batch_summary.sql
- ✅ 基本查詢功能
- ✅ 搜尋條件測試
- ✅ 分頁功能
- ✅ 計算邏輯驗證（銷售率、FCR、週齡等）
- ✅ 日期計算（到期日）
- ✅ 資料串接（飼料名稱）
- ✅ 排序邏輯
- ✅ 空結果處理

### 2. sales_query.sql
- ✅ 基本查詢功能
- ✅ 搜尋功能（批次名稱、客戶）
- ✅ 計算邏輯（平均價格、重量計算）
- ✅ 排序和分頁
- ✅ NULL 值處理

### 3. count_data_query.sql
- ✅ 基本計數查詢
- ✅ 條件計數（event_id）
- ✅ 不同表格計數
- ✅ 空表計數

## 運行測試

### 運行所有 SQL 測試
```bash
uv run pytest tests/sql/ -v
```

### 運行特定測試文件
```bash
uv run pytest tests/sql/test_batch_summary.py -v
```

### 運行特定測試
```bash
uv run pytest tests/sql/test_batch_summary.py::TestBatchSummarySQL::test_batch_summary_basic_query -v
```

### 使用測試運行器
```bash
uv run python tests/sql/test_runner.py
```

## 測試架構

### Fixtures
- `test_db`: 創建臨時 SQLite 測試資料庫
- `sql_templates`: Jinja2 SQL 模板引擎
- `sample_data`: 插入測試數據到資料庫

### 測試數據
測試使用模擬的農場數據：
- **breed 表**: 繁殖記錄（古早雞、閹雞等）
- **sale 表**: 銷售記錄（客戶、價格、重量等）
- **farm_production 表**: FCR 數據
- **feed 表**: 飼料供應商數據

### 測試類別
每個 SQL 文件對應一個測試類：
- `TestBatchSummarySQL`: 批次摘要查詢測試
- `TestSalesQuerySQL`: 銷售查詢測試
- `TestCountDataQuerySQL`: 計數查詢測試

## 新增測試

當新增 SQL 查詢時，請遵循以下步驟：

1. 在 `tests/sql/` 目錄建立對應的測試文件：`test_new_query.py`
2. 創建測試類：`TestNewQuerySQL`
3. 如需特殊測試數據，在 `conftest.py` 中新增 fixture
4. 測試應該覆蓋：
   - 基本查詢功能
   - 條件查詢
   - 計算邏輯
   - 邊界情況
   - 錯誤處理

## 注意事項

- 所有測試使用獨立的臨時資料庫，不會影響實際數據
- 測試數據在每次測試後自動清理
- SQL 模板通過 Jinja2 渲染，支持條件邏輯測試
- 測試覆蓋複雜的 CTE 查詢和計算邏輯