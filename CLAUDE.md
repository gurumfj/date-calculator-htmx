# CleanSales Backend AI 工作流記憶檔

## 🎯 項目概覽
**專案名稱**: CleanSales Backend  
**技術棧**: Python (uv) + FastAPI + SQLite + HTMX + TailwindCSS  
**開發模式**: 測試驅動 + 漸進重構 + 編輯優先  

## 🚨 強制性約束 (AI 必須遵守)

### 資料庫操作
- ✅ **必須**: 使用 `src/db_init.py` API
- ❌ **禁止**: 直接 `sqlite3.connect()`
- ✅ **優先**: `get_db_connection_context()` 上下文管理器
- ✅ **必須**: SQL 查詢使用明確欄位名，禁止 `SELECT *`
- ℹ️ **資訊**: WAL 模式，支援並發，無需手動鎖或 commit

### 開發約束
- 🧪 **測試優先**: 任何修改前後都要跑 `uv run pytest tests/sql/ -v`
- ✂️ **簡化優先**: 移除複雜度 > 優化性能
- 📝 **編輯優先**: 編輯現有文件 > 創建新文件
- 🤔 **質疑設計**: 避免過度設計（如不必要的單例模式）

## ⚙️ 技術棧配置

### 核心環境
```bash
# Python 管理器
uv

# 標準運行命令
uv run [command]

# 測試命令
uv run pytest tests/sql/ -v
```

### 架構組件
- **後端**: FastAPI + SQLite + WAL
- **前端**: HTMX + Alpine.js + TailwindCSS  
- **模板**: Jinja2
- **測試**: pytest + 內存資料庫

## 📋 標準工作流

### 1. SQL 模板測試工作流 🚨

#### 測試覆蓋現況
**已覆蓋** ✅:
- batch_summary.sql → test_batch_summary.py
- count_data_query.sql → test_count_data_query.py  
- sales_query.sql → test_sales_query.py

**缺失測試** ❌:
- farm_production.sql
- feed.sql
- get_batch_statistics.sql
- get_data_query.sql
- get_event_details.sql
- get_upload_events.sql

#### SQL 模板測試要求
```
每個 SQL 模板必須有對應測試文件：
1. 測試參數化查詢正確性
2. 測試邊界條件和異常情況  
3. 驗證 JSON 結構和資料完整性
4. 確保性能符合預期
```

#### 新增 SQL 模板測試流程
```
1. 創建 test_[template_name].py
2. 設置內存資料庫測試環境
3. 準備測試資料集
4. 編寫多種場景測試用例
5. 執行並確保通過：uv run pytest tests/sql/ -v
```

### 2. Context7 文檔查詢工作流

#### 執行步驟
```
1. 識別需求 → 明確技術/庫名稱
2. resolve-library-id → 獲取正確庫標識符  
3. get-library-docs → 取得最新文檔
```

#### 項目常用庫
- `FastAPI` - 後端 API 開發
- `SQLite` - 資料庫操作
- `HTMX` - 前端互動

### 3. SVG 圖標快速參考

#### 位置與使用
- 文件：`src/server/templates/macros/_icons.html`
- 使用：`{% from 'macros/_icons.html' import ... %}`
- 格式：統一 viewBox="0 0 24 24"
- 分類：編輯/導航/文件/狀態圖標

### 4. 開發任務執行工作流

#### 任務開始檢查清單
- [ ] 讀取並理解需求
- [ ] 檢查相關測試：`uv run pytest tests/sql/ -v`
- [ ] 確認檔案結構和依賴關係
- [ ] 識別需要編輯的現有文件

#### 實施步驟
```
1. 分析現有代碼 → 理解當前實現
2. 設計最小變更 → 符合編輯優先原則
3. 實施變更 → 遵守強制約束
4. 執行測試 → 確保無回歸
5. 文檔更新 → 如有必要
```

#### 任務完成檢查清單
- [ ] 所有測試通過
- [ ] 代碼符合項目約束
- [ ] 沒有過度設計
- [ ] 相關文檔已更新

## 📂 文件系統導覽

### 項目結構
```
src/
├── server/              # 🆕 新功能開發區
│   ├── templates/sql/   # SQL 查詢模板
│   ├── templates/       # HTML 模板
│   └── static/          # 靜態資源
└── cleansales_backend/  # 🔄 舊代碼重構區
```

### 關鍵文件
- `data/sqlite.db` - 🗄️ 主資料庫
- `src/db_init.py` - 🔧 資料庫連接 API
- `tests/sql/` - 🧪 SQL 測試套件
- `tasks.md` - 📋 任務清單 (定期重新評估)
- `pyproject.toml` - ⚙️ 項目配置

### 模板系統
- `src/server/templates/macros/_icons.html` - 🎨 SVG 圖標庫
- `src/server/templates/` - 📄 Jinja2 模板

## ⚡ 快速參考

### 常用指令
```bash
# 運行測試 (必須)
uv run pytest tests/sql/ -v

# 檢查配置
cat pyproject.toml

# 啟動開發服務器
uv run [start_command]
```

### 決策樹

#### 需要添加新功能時
```
新功能需求
├── 是否涉及新 SQL 模板？
│   ├── 是 → 創建模板 + 必須編寫測試
│   └── 否 → 繼續
├── 是否需要資料庫操作？
│   ├── 是 → 使用 db_init.py API + 編寫測試
│   └── 否 → 繼續
├── 是否需要新文件？
│   ├── 是 → 考慮編輯現有文件
│   └── 否 → 編輯現有文件
└── 實施 → 測試 → 完成
```

#### 遇到技術問題時
```
技術問題
├── 是否為已知技術棧？
│   ├── 是 → 檢查項目現有實現
│   └── 否 → 使用 Context7 查詢文檔
├── 是否需要最新資訊？
│   ├── 是 → Context7 查詢
│   └── 否 → 檢查項目歷史
└── 實施解決方案 → 測試驗證
```

## 🎯 AI 執行指引

1. **SQL 模板測試優先** - 任何 SQL 相關變更必須有測試覆蓋
2. **檢查強制約束** - 始終遵守資料庫和開發約束
3. **測試驅動開發** - 修改前後都要執行完整測試
4. **Context7 查詢** - 主動獲取最新技術資訊
5. **簡化思維** - 質疑複雜設計，優先編輯現有文件
6. **補強測試覆蓋** - 優先處理缺失的 SQL 模板測試

---
*本檔案為 AI 工作記憶檔，應保持最新且結構化*