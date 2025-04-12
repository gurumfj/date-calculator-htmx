# CleanSales 前端開發任務清單

## 移動端優化 (已完成)

### 已完成任務
- [x] 實現移動優先 (Mobile-First) 的設計方法
- [x] 優化 BatchListItem 實現全屏詳情顯示
  - [x] 桌面端保持展開卡片式設計
  - [x] 移動端使用全屏模態對話框
  - [x] 實現 URL 哈希機制支援批次直接跳轉和分享功能
  - [x] 添加滑動手勢支援下滑關閉模態框
- [x] 添加選項卡式導航來整理批次詳情
  - [x] 批次資訊頁籤
  - [x] 銷售資訊頁籤
  - [x] 飼料記錄頁籤
- [x] 優化移動端表格和分頁控制
  - [x] 為移動端提供卡片式列表代替寬表格
  - [x] 改進分頁控制元件，適配觸控操作
- [x] 改進 TopCard 組件的視覺提示
  - [x] 添加更醒目的點擊提示
  - [x] 區分移動端和桌面端的提示樣式
- [x] 修復 TypeScript 編譯錯誤
  - [x] 解決 `Dialog.Overlay` 錯誤
- [x] 添加移動端篩選功能
  - [x] 實現頂部篩選按鈕和篩選面板
  - [x] 使用 BatchFilter 組件提供統一的搜尋和篩選功能
  - [x] 確保篩選條件反映在UI上
  - [x] 解決搜尋和篩選按鈕重複問題，優化使用者體驗

### 主要組件更新
- `MobileLayout`: 增加頂部和底部導航欄，添加標籤式內容切換，整合篩選功能
- `BatchListItem`: 添加響應式佈局，針對不同屏幕尺寸採用不同顯示方式
- `SalesRawTable`: 優化移動端表格顯示和分頁控制
- `TopCard`: 添加更明確的點擊/展開提示
- `BatchFilter`: 適配移動端顯示，提供精簡的過濾UI，整合搜尋和篩選功能於一體

### 技術實現要點
- 使用 Tailwind CSS 的斷點系統 (md:hidden, hidden md:block) 實現響應式設計
- 使用 @headlessui/react 的 Dialog 和 Transition 組件實現全屏模態框
- 使用 URL 哈希機制 (#batch/批次名稱) 支援直接訪問特定批次
- 添加觸控手勢支援，提升移動端使用體驗
- 使用 React 狀態管理 (useState) 控制UI元素的顯示/隱藏
- 簡化使用者介面，減少冗餘功能按鈕

## 未來待辦事項
- [x] 完善底部導航欄功能
  - [x] 實現首頁儀表盤
  - [x] 實現報表頁面
  - [x] 實現設定頁面
- [x] 添加下拉刷新功能
- [ ] 優化移動端圖表顯示
- [ ] 考慮添加頁面動畫效果
- [ ] 進一步優化大型表格在移動端的顯示方式
- [x] 改進深色模式支援
- [ ] 分析並優化代碼包大小，減少首次載入時間

## 相關技術參考
- Tailwind CSS 移動優先設計: https://tailwindcss.com/docs/responsive-design
- Headless UI 組件庫: https://headlessui.dev/
- React 性能優化: https://react.dev/learn/rendering-lists
