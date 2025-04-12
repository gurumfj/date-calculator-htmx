# CleanSales前端元件重構分支工作流程

## 1. 重構分支說明

`refactor/trunk-components` 分支是一個專門用於前端元件目錄結構重構的長期分支。該分支遵循Trunk-Based Development的理念，但專注於程式碼組織和結構的改進，而非功能開發。

### 分支目的

- 維護清晰一致的元件目錄結構
- 集中管理所有元件路徑相關的重構
- 降低元件重構對主分支的影響
- 確保所有元件遵循相同的組織規範

## 2. 目錄結構標準

本分支維護以下標準目錄結構：

```
src/components/
├── common/           # 通用元件 (可跨功能重用的基礎元件)
│   └── [ComponentName]/
│       └── index.tsx
├── layout/           # 佈局相關元件 (頁面結構、導航等)
│   └── [ComponentName]/
│       └── index.tsx
├── features/         # 功能相關元件 (按業務功能分組)
│   ├── batch/        # 批次相關元件
│   ├── sales/        # 銷售相關元件
│   └── feed/         # 飼料相關元件
│       └── [ComponentName]/
│           └── index.tsx
└── ui/               # UI元件 (視覺呈現、圖表等)
    └── charts/       # 圖表相關元件
        └── [ComponentName]/
            └── index.tsx
```

## 3. 工作流程

### 3.1 分支操作

**1. 更新分支**

每次在此分支工作前，先從主分支同步最新代碼：

```bash
# 確保本地有最新的主分支代碼
git checkout main
git pull

# 切換到重構分支並合併主分支變更
git checkout refactor/trunk-components
git merge main
```

**2. 解決衝突**

如果合併時出現衝突，優先保留重構分支的目錄結構：

```bash
# 解決衝突後
git add .
git commit -m "合併: 更新主分支變更並維持元件目錄結構"
```

### 3.2 重構流程

**1. 分析階段**

先分析需要重構的元件，確定它們的功能分類：

- 建立待重構元件清單
- 確定每個元件應屬於哪個目錄類別
- 檢查元件間的依賴關係

**2. 遷移階段**

遵循以下步驟遷移元件：

```bash
# 1. 創建新的目錄結構
mkdir -p src/components/[category]/[ComponentName]

# 2. 複製元件到新位置，命名為index.tsx
cp src/components/[OldPath].tsx src/components/[category]/[ComponentName]/index.tsx

# 3. 更新導入路徑
# 在編輯器中打開文件，更新所有相對導入路徑
```

**3. 測試階段**

每完成一組相關元件的遷移後，進行測試：

```bash
# 運行TypeScript檢查
bun run typecheck

# 如果有單元測試，運行測試
bun run test

# 啟動開發服務器測試功能
bun run dev
```

**4. 清理階段**

確認新元件工作正常後，移除舊元件：

```bash
# 使用git rm移除舊文件
git rm src/components/[OldPath].tsx

# 提交變更
git commit -m "移除: 已遷移到新結構的舊元件文件"
```

### 3.3 合併回主分支

當完成一組相關元件的重構後，將變更合併回主分支：

```bash
# 1. 確保本地分支是最新的
git pull origin refactor/trunk-components

# 2. 推送到遠端倉庫
git push origin refactor/trunk-components

# 3. 建立Pull Request或直接合併
# (根據專案具體流程)

# 4. 合併完成後保留分支，不要刪除
```

## 4. 重構指南

### 4.1 元件命名和組織規範

- 元件目錄使用PascalCase命名（例如：`BatchFilter`）
- 主元件文件命名為`index.tsx`
- 子元件可放在同一目錄下，使用描述性名稱（例如：`DetailView.tsx`）
- 每個元件目錄可包含相關的樣式、測試、工具函數等

### 4.2 導入路徑規範

優先使用絕對路徑導入（從專案根目錄開始）：

```typescript
// 推薦
import { Something } from "src/components/common/Something";

// 次選
import { Something } from "../../../../components/common/Something";
```

如可能，考慮配置TypeScript路徑別名簡化導入：

```typescript
// 在tsconfig.json中配置path後
import { Something } from "@common/Something";
```

### 4.3 代碼審查重點

重構時需要關注的重點：

1. **路徑完整性**：確保所有導入路徑都已更新
2. **功能完整性**：確保功能不受重構影響
3. **一致性**：確保元件分類準確且一致
4. **無冗餘**：移除不再使用的舊文件和導入
5. **測試覆蓋**：確保測試仍能通過

### 4.2 路徑別名（Path Alias）使用指南

#### 4.2.1 配置路徑別名

在 `tsconfig.json` 中配置路徑別名：

```json
{
  "compilerOptions": {
    "baseUrl": ".",
    "paths": {
      "@components/*": ["src/components/*"],
      "@hooks/*": ["src/hooks/*"],
      "@contexts/*": ["src/contexts/*"],
      "@services/*": ["src/services/*"],
      "@utils/*": ["src/utils/*"],
      "@app-types/*": ["src/types/*"]
    }
  }
}
```

#### 4.2.2 路徑別名使用規範

1. **優先使用路徑別名**：
```typescript
// 建議使用
import { Button } from "@components/common/Button";
import { useBatchFilter } from "@hooks/useBatchFilter";

// 避免使用
import { Button } from "../../../components/common/Button";
import { useBatchFilter } from "../../../../hooks/useBatchFilter";
```

2. **路徑別名對應表**：
- `@components/*` - 元件目錄
- `@hooks/*` - Hook 函數目錄
- `@contexts/*` - Context 相關檔案
- `@services/*` - 服務層檔案
- `@utils/*` - 工具函數
- `@app-types/*` - TypeScript 類型定義

3. **元件導入規則**：
```typescript
// 通用元件
import { LoadingSpinner } from "@components/common/LoadingSpinner";

// 佈局元件
import { DesktopLayout } from "@components/layout/DesktopLayout";

// 功能元件
import { BatchFilter } from "@components/features/batch/BatchFilter";

// UI 元件
import { SalesChart } from "@components/ui/charts/SalesChart";
```

4. **批量導入規範**：
```typescript
// 建議：明確導入需要的元件
import { Button, Card, Input } from "@components/common";

// 避免：使用通配符導入
import * as CommonComponents from "@components/common";
```

#### 4.2.3 路徑別名遷移步驟

1. 識別需要更新的文件
2. 使用搜尋工具找出所有相對路徑導入
3. 將相對路徑替換為對應的路徑別名
4. 執行 TypeScript 檢查確保無誤
5. 更新相關測試文件

#### 4.2.4 常見問題處理

1. **路徑別名不生效**：
   - 檢查 `tsconfig.json` 配置
   - 確認 webpack/vite 配置已同步更新
   - 重啟開發服務器

2. **測試文件路徑問題**：
   - 確保 Jest/Vitest 配置支援路徑別名
   - 更新測試文件中的導入路徑

3. **編輯器提示問題**：
   - 安裝相關 IDE 插件
   - 重新載入 TypeScript 服務

## 5. 文檔維護

### 5.1 元件目錄文檔

維護一個元件目錄文檔，記錄所有元件的位置和用途：

```markdown
# 元件目錄

## 通用元件 (common/)
- `LoadingSpinner` - 載入中指示器
- `EmptyState` - 空數據狀態顯示
...

## 功能元件 (features/)
### 批次相關 (batch/)
- `BatchFilter` - 批次過濾器
...
```

### 5.2 重構日誌

每次重構操作都應記錄在重構日誌中：

```markdown
# 重構日誌

## 2025-04-03
- 遷移所有銷售相關元件到 features/sales/
- 更新相關導入路徑
- 移除舊元件文件

## 2025-05-10
- 遷移新增的批次管理元件到 features/batch/
...
```

## 6. 注意事項和最佳實踐

1. **漸進式重構**：一次處理一小組相關元件，而非所有元件
2. **提交信息**：使用清晰的前綴（例如：`重構:`, `移除:`, `更新:`）
3. **保持同步**：定期從主分支合併最新變更
4. **代碼評審**：重要的重構應該進行代碼評審
5. **測試覆蓋**：確保所有重構都有充分的測試覆蓋
6. **文檔更新**：及時更新相關文檔
7. **遷移先於移除**：先確認新元件正常工作，再移除舊元件

## 7. 回退策略

如果重構遇到問題，可採用以下回退策略：

```bash
# 回退最後一次提交
git reset --soft HEAD~1

# 或完全回退（包括工作區變更）
git reset --hard HEAD~1

# 如果已合併到主分支，可以建立新提交修復問題
git commit -m "修復: 解決元件重構導致的問題"
```

---

本工作流程文檔應隨著項目演進定期更新。

**最後更新**：2025-04-03
