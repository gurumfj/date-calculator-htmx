# 專案開發指南

## 環境與工具
主動檢查專案裡的pyproject.toml了解環境部署方式
python運行環境是uv run
本專案的python管理器是uv, 測試運行使用uv run

## 前端技術規範
html元素選用需要依照html5的語義建議,例如details, summary, main, section, aside, form...以及更多，千萬別只使用div
從base.html確認網頁載入的技術, 本專案基本載入htmx, alpine.js, taiwildcss or picocss

## 測試指引
用pytest覆蓋sql測試
運行測試: uv run pytest tests/sql/ -v
所有測試必須使用SQLite內存資料庫,避免外部依賴

## 代碼架構
src/cleansales_backend/* 是要被重構更新的代碼, 重構功能要移出這個資料夾
新功能統一放在src/server/目錄下
SQL查詢模板統一放在src/server/templates/sql/
HTML模板統一放在src/server/templates/

## 重要約定
- 絕不創建新文件除非必要,優先編輯現有文件
- 提交代碼前必須運行測試確保通過
- HTMX無限滾動使用revealed觸發器
- 表單整合使用unified form結構
- 數據庫查詢使用Jinja2模板渲染SQL
- 分頁查詢統一使用LIMIT/OFFSET模式