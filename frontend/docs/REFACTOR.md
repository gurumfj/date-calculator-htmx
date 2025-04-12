# 重構日誌

## 2024-03-19
- 建立標準元件目錄結構文檔
- 完成元件目錄清單整理
- 設置並統一使用路徑別名：
  - @components
  - @hooks
  - @contexts
  - @services
  - @utils
  - @layouts
  - @app-types
- 更新所有元件的 import 路徑，使用路徑別名替代相對路徑
- 修正 TypeScript 配置，支援 Node.js 類型
- 將佈局元件從 src/layouts 移動到 src/components/layout：
  - DesktopLayout
  - MobileLayout
- 更新佈局元件的 import 路徑
- 更新元件目錄文檔，添加新移動的佈局元件

### 待完成事項
- [ ] 檢查並更新所有測試文件的路徑
- [ ] 確保所有元件都有適當的文檔說明
- [ ] 檢查並更新所有相關的 storybook 文件
