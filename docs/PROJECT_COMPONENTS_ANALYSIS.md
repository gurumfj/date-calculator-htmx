# CleanSales前端專案組件分析

本文件提供CleanSales前端專案的組件結構分析，包括使用的和未使用的組件，以及整體路由結構。

## 專案路由結構

```
Router (src/router/index.tsx)
├── App (src/App.tsx) - 根佈局容器
│   ├── HomePage (src/pages/HomePage.tsx) - 首頁/儀表板
│   ├── BatchesPage (src/pages/BatchesPage.tsx) - 批次列表頁
│   ├── BatchDetailPage (src/pages/BatchDetailPage.tsx) - 批次詳情頁
│   ├── ReportsPage (src/pages/ReportsPage.tsx) - 報表頁
│   ├── SettingsPage (src/pages/SettingsPage.tsx) - 設定頁
│   └── NotFoundPage (src/pages/NotFoundPage.tsx) - 404頁面
```

## 核心應用組件

### 入口與路由
- `main.tsx` - 應用入口點，渲染RouterProvider
- `router/index.tsx` - 路由配置
- `App.tsx` - 根組件，提供全局上下文和佈局結構

### 頁面組件
- `pages/HomePage.tsx` - 首頁/儀表板頁面
- `pages/BatchesPage.tsx` - 批次列表頁面
- `pages/BatchDetailPage.tsx` - 批次詳情頁面
- `pages/ReportsPage.tsx` - 報表頁面
- `pages/SettingsPage.tsx` - 設定頁面
- `pages/NotFoundPage.tsx` - 404錯誤頁面

### 佈局組件
- `components/layout/AppLayout.tsx` - 應用主佈局
- `components/layout/BreedToggle/index.tsx` - 品種切換組件
- `components/layout/FeatureFlagsPanel/index.tsx` - 特性標誌面板

## 功能組件

### 批次相關組件 (`components/features/batch/`)
- `BatchFilter/index.tsx` - 批次過濾器
- `BatchListItem/index.tsx` - 批次列表項
- `BatchListItem/TopCard.tsx` - 批次列表項頂部卡片
- `BatchListItem/DetailCard.tsx` - 批次列表項詳情卡片

### 儀表板組件 (`components/features/dashboard/`)
- `index.tsx` - 儀表板導出
- `Dashboard.tsx` - 儀表板主組件

### 報表組件 (`components/features/reports/`)
- `index.tsx` - 報表導出
- `SimpleReport.tsx` - 簡單報表組件

### 設定組件 (`components/features/settings/`)
- `index.tsx` - 設定導出
- `Settings.tsx` - 設定主組件

## 通用組件

### 通用UI組件 (`components/common/`)
- `NotificationBar.tsx` - 通知條
- `PullToRefresh/index.tsx` - 下拉刷新組件

## 數據處理

### 鉤子函數(Hooks)
- `hooks/useBatchData.tsx` - 批次數據處理鉤子
- `hooks/useBatchFilter.ts` - 批次過濾鉤子
- `hooks/useEnhancedFetchData.ts` - 增強的數據獲取鉤子

### 上下文(Contexts)
- `contexts/NotificationContext.tsx` - 通知上下文
- `contexts/ThemeContext.tsx` - 主題上下文

## 當前未使用的組件

以下組件在現有路由架構中沒有被直接使用，可能用於舊版佈局或將來功能：

### 佈局組件
- `components/layout/DesktopLayout/index.tsx` - 桌面佈局
- `components/layout/MobileLayout/index.tsx` - 移動設備佈局

### 批次相關
- `components/features/batch/BatchCard/index.tsx` - 批次卡片
- `components/features/batch/BatchDetail/index.tsx` - 批次詳情
- `components/features/batch/BatchDetailPanel/index.tsx` - 批次詳情面板
- `components/features/batch/BreedFilter/index.tsx` - 品種過濾器

### 圖表組件 (`components/ui/charts/`)
- `CustomerWeightPieChart/index.tsx` - 客戶重量餅圖
- `SalesCalendarChart/index.tsx` - 銷售日曆圖
- `SalesCountChart/index.tsx` - 銷售計數圖
- `WeightChart/index.tsx` - 重量圖

### 銷售相關 (`components/features/sales/`)
- `EnhancedSalesChart/index.tsx` - 增強銷售圖表
- `SalesChart/index.tsx` - 銷售圖表
- `SalesChartDashboard/index.tsx` - 銷售圖表儀表板
- `SalesDataTable/index.tsx` - 銷售數據表
- `SalesRawContent/index.tsx` - 原始銷售內容
- `SalesRawTable/index.tsx` - 原始銷售表格
- `SalesReport/index.tsx` - 銷售報表
- `SalesSummaryCards/index.tsx` - 銷售摘要卡片

### 飼料相關 (`components/features/feed/`)
- `FeedRecordTable/index.tsx` - 飼料記錄表

### 通用組件
- `components/common/DarkModeToggle/index.tsx` - 暗黑模式切換
- `components/common/EmptyState/index.tsx` - 空狀態
- `components/common/InfoCard/index.tsx` - 信息卡片
- `components/common/LoadingSpinner/index.tsx` - 加載轉環
- `components/common/SearchBar/index.tsx` - 搜索欄

## 優化建議

1. **組件重用**: 將未使用的組件整合到新的路由架構中，或者移除不需要的組件。
2. **代碼拆分**: 為大型頁面實現代碼拆分，以提高初始加載性能。
3. **組件命名**: 標準化組件命名約定，統一使用單獨文件或index.tsx。
4. **測試覆蓋**: 為關鍵組件添加單元測試，確保穩定性。

## 待辦事項

- [ ] 審查並整合未使用的組件
- [ ] 標準化組件導入路徑
- [ ] 為長期未使用的組件設置棄用計劃
- [ ] 實現更完整的代碼拆分策略
- [ ] 為所有頁面添加適當的錯誤邊界
