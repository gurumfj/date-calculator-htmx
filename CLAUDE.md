# CleanSales Backend 開發指南

## 核心環境
- Python 管理器：`uv`
- 運行命令：`uv run`
- 測試命令：`uv run pytest tests/sql/ -v`

## 資料庫連接（重要）
- **必須**使用 `src/db_init.py` 的 API，禁止直接 `sqlite3.connect()`
- **優先**使用 `get_db_connection_context()` 上下文管理器
- 資料庫使用 WAL 模式，支援並發，無需手動鎖或 commit
- SQL 查詢**必須**使用明確欄位名稱，禁止 `SELECT *`

## 專案結構
```
src/
├── server/              # 新功能放這裡
│   ├── templates/sql/   # SQL 查詢模板
│   └── templates/       # HTML 模板
└── cleansales_backend/  # 舊代碼，待重構移出
```

## 開發原則
- **測試優先**：任何修改前後都要跑測試
- **簡化優先**：移除複雜度比優化更重要
- **編輯優先**：盡量編輯現有文件而非創建新文件
- **質疑設計**：避免過度設計（如不必要的單例模式）

## 技術棧
- 後端：FastAPI + SQLite + WAL
- 前端：HTMX + Alpine.js + TailwindCSS
- 模板：Jinja2

## 重要文件
- `data/sqlite.db` - 主資料庫
- `tasks.md` - 任務清單，定期重新評估優先順序
- `tests/sql/` - SQL 測試，使用內存資料庫

## 常用指令
```bash
# 運行測試
uv run pytest tests/sql/ -v

# 檢查專案配置
cat pyproject.toml
```