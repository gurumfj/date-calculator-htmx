# Cleansales Backend - 開發進度記錄

## 專案概述
養雞場批次管理系統，使用 FastHTML + Tailwind CSS + Alpine.js + HTMX 技術棧

## 最新進度 (2025-06-15)

### 已完成功能

#### 1. 頁面美化和佈局
- ✅ 導入 Tailwind CSS 美化整體版面
- ✅ 漸層背景設計 (`bg-gradient-to-br from-blue-50 to-indigo-100`)
- ✅ 現代化卡片設計和陰影效果
- ✅ 響應式網格佈局

#### 2. 導航系統優化
- ✅ 品種選擇導航（黑羽、古早、舍黑、閹雞）
- ✅ Alpine.js 狀態管理 (`activeBreed` 狀態)
- ✅ 動態樣式切換，顯示當前選中品種
- ✅ 可展開/收合的日期選擇器（進階篩選功能）
- ✅ 語義化 `<nav>` 結構，包含 Header 和 Section

#### 3. 資料查詢功能
- ✅ 新增 FCR 欄位查詢（來自 farm_production 表）
- ✅ SQL JOIN farm_production 表取得 FCR 資料
- ✅ 查詢邏輯從 offset/limit 改為日期參數（30天區間查詢）
- ✅ 動態顏色編碼：
  - 銷售率：≥80%(綠) ≥50%(黃) <50%(紅)
  - FCR：≤2.6(綠) ≤3.0(黃) >3.0(紅)

#### 4. 可展開批次元件
- ✅ 使用語義化 HTML 結構：
  - `<article>` 包裝整個批次項目
  - `<header>` 摘要資訊區域
  - `<section>` 詳細資訊區域
- ✅ 上半部：摘要資訊
  - 預留最多5個grid空間的動態資料顯示
  - 當前顯示：飼養日期、到期日期、總飼養數、銷售率、FCR
- ✅ 下半部：詳細資訊（Mock資料UI）
  - 飼養詳情（雄雞/雌雞數量、平均重量）
  - 銷售記錄表格
  - 生產分析圖表預留區域

#### 5. 互動效果和動畫
- ✅ HTMX 淡入淡出過渡效果 (`hx_swap="innerHTML transition:true"`)
- ✅ Alpine.js 控制的展開/收合動畫：
  - 使用 `max-height` 和 `opacity` 實現平滑縮放
  - 300ms 過渡動畫
- ✅ 箭頭圖示旋轉動畫
- ✅ 狀態保持和視覺反饋

### 技術架構

#### 前端技術
- **FastHTML**: 服務端渲染框架
- **Tailwind CSS**: 樣式框架
- **Alpine.js**: 前端狀態管理和互動
- **HTMX**: 動態內容載入和過渡效果

#### 後端技術
- **Python**: 主要開發語言
- **SQLite**: 資料庫
- **UV**: Python 環境管理工具

#### 資料表結構
- `breed`: 飼養資料（batch_name, chicken_breed, breed_date, breed_male, breed_female）
- `sale`: 銷售資料（batch_name, male_count, female_count）
- `farm_production`: 農場生產資料（batch_name, fcr）

### 文件結構
```
src/cleansales_backend/web/
├── batch_route_v2.py    # 主要批次管理路由
├── main.py              # 主應用入口
├── data_service.py      # 資料庫服務
├── file_upload_handler.py # 文件上傳處理
└── resources.py         # 共用資源
```

### 待解決問題
- ❌ 載入更多功能的重複資料問題
  - 目前30天區間查詢可能導致重複顯示批次
  - 需要重新設計分頁邏輯或實作前端去重

### 下一步開發計劃
1. 解決載入更多的重複資料問題
2. 實作下半部詳細資訊的真實資料查詢路由
3. 完善生產分析圖表功能
4. 新增批次編輯和管理功能
5. 實作資料匯出功能

### 重要設定
- 主分支：`main`
- 當前開發分支：`dev`
- Python 運行環境：`uv run`
- 專案部署方式：參考 `pyproject.toml`

---
*最後更新：2025-06-15*