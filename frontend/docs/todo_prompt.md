# AI 執行任務

## 目標
將`filterbatches` array從`App.tsx`傳遞到`SalesReport.tsx`，並確保`SalesReport`組件能夠正確接收和使用該數據。
### 狀態：已完成 (2025-03-22 00:10)

## 步驟
1. 在`App.tsx`中，找到`filteredBatches`的定義位置。
2. 將`filteredBatches`作為prop傳遞給`SalesReport`組件。
3. 在`SalesReport.tsx`中，更新`SalesReportProps`接口，添加`filteredBatches`屬性。
4. 在`SalesReport`組件中，使用傳入的`filteredBatches`數據來渲染圖表。

## 額外任務
讓`searchbar`和`datepicker`在`SalesReport` tab也能使用。

### 狀態：已完成 (2025-03-22 00:15)

### 步驟
1. 在`App.tsx`中，將`searchbar`和`datepicker`的邏輯提取到一個獨立的組件中，以便在`batch`和`sales` tab中都能使用。
2. 確保`searchbar`和`datepicker`的狀態在tab切換時保持一致。
3. 更新`SalesReport`組件，使其能接收`searchbar`和`datepicker`的相關props。

## 新任務：簡化日期計算和轉換的代碼

### 目標
使用方便的日期處理套件來簡化`dateUtils.ts`中的日期計算和轉換邏輯。

### 狀態：已完成 (2025-03-22 00:15)

### 步驟
1. 選擇一個適合的日期處理套件（例如`date-fns`或`dayjs`）。
2. 更新`dateUtils.ts`中的`calculateDayAge`和`calculateWeekAge`函數，使用套件提供的功能來簡化代碼。
3. 確保所有使用這些函數的組件都能正確運作。

### 注意事項
- 選擇的套件應與現有代碼兼容。
- 確保新引入的套件不會增加過多的包大小。
- 添加必要的註釋以解釋代碼變更。

## 注意事項
- 確保類型定義正確。
- 保持代碼的簡潔性和可讀性。
- 添加必要的註釋以解釋代碼變更.

### Search Bar and DatePicker UI in Navbar Expand Canvas

1. **在Navbar中新增展開式Canvas**
   - 在Navbar組件中新增Canvas的顯示狀態控制
   - 新增Canvas的展開/收起動畫
   - 確保Canvas在不同屏幕尺寸下的響應式設計

2. **整合SearchBar和DatePicker到Canvas**
   - 將SearchBar和DatePicker的props傳遞到Canvas
   - 調整SearchBar和DatePicker的佈局和樣式
   - 確保SearchBar和DatePicker的功能正常運作

3. **處理Canvas與其他組件的互動**
   - 確保Canvas的展開不會影響其他Navbar元素
   - 處理Canvas與SearchBar、DatePicker的互動邏輯
   - 確保Canvas的收起時狀態重置

### Move BreedToggle to SearchAndDateFilter

1. **將BreedToggle組件移到SearchAndDateFilter組件中**
   - 修改SearchAndDateFilter組件，新增BreedToggle的props
   - 將BreedToggle的邏輯從App.tsx移到SearchAndDateFilter組件中
   - 確保BreedToggle的樣式和功能正常運作

2. **處理響應式設計**
   - 確保BreedToggle在不同屏幕尺寸下的顯示效果
   - 調整BreedToggle與SearchAndDateFilter的佈局

3. **更新相關的狀態管理**
   - 將BreedToggle的狀態管理移到SearchAndDateFilter組件中
   - 確保狀態更新不會影響其他功能
