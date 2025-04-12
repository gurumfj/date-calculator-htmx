# CleanSales Supabase 整合指南

本文檔提供了在CleanSales前端專案中整合和使用Supabase的完整指南。

## 目錄

1. [簡介](#簡介)
2. [設置](#設置)
3. [環境變數配置](#環境變數配置)
4. [檔案結構](#檔案結構)
5. [文檔](#文檔)
6. [示例與使用方法](#示例與使用方法)
7. [測試](#測試)
8. [部署](#部署)
9. [常見問題](#常見問題)

## 簡介

CleanSales專案現在整合了Supabase作為數據存儲和實時更新的解決方案。Supabase是一個開源的Firebase替代方案，提供以下功能：

- PostgreSQL資料庫服務
- 身份驗證
- 實時數據更新
- 存儲服務
- 邊緣函數

這個整合允許我們在前端直接與Supabase資料庫進行交互，減少了對後端API的依賴。

## 設置

### 依賴安裝

確保已安裝必要的Supabase依賴：

```bash
bun add @supabase/supabase-js
```

### Supabase專案設置

1. 登入[Supabase控制台](https://app.supabase.io/)
2. 創建新專案或使用現有專案
3. 獲取專案URL和匿名金鑰（API > URL和anon/public）
4. 創建必要的資料表（參考`src/tstype.ts`中的類型定義）

### 前端設置

1. 將Supabase環境變數添加到`.env.local`文件：
   ```
   VITE_SUPABASE_URL=YOUR_SUPABASE_URL
   VITE_SUPABASE_ANON_KEY=YOUR_SUPABASE_ANON_KEY
   ```

2. 創建Supabase客戶端配置：
   ```typescript
   // src/utils/supabaseClient.ts
   import { createClient } from '@supabase/supabase-js'
   import type { Database } from '../tstype'

   const supabaseUrl = import.meta.env.VITE_SUPABASE_URL
   const supabaseAnonKey = import.meta.env.VITE_SUPABASE_ANON_KEY

   export const supabase = createClient<Database>(supabaseUrl, supabaseAnonKey)
   ```

## 環境變數配置

專案使用以下環境變數：

| 變數名 | 說明 | 必須 |
|--------|------|------|
| VITE_SUPABASE_URL | Supabase專案URL | 是 |
| VITE_SUPABASE_ANON_KEY | Supabase匿名金鑰 | 是 |
| VITE_API_URL | 舊版API URL（如果需要） | 否 |

確保這些變數在不同環境中都正確設置：

- 開發環境： `.env.local`
- 生產環境： `.env.production` 或部署環境變數

## 檔案結構

以下是Supabase相關檔案的結構：

```
/frontend
  ├── src/
  │   ├── utils/
  │   │   └── supabaseClient.ts        // Supabase客戶端配置
  │   ├── hooks/
  │   │   ├── useSupabase.ts           // 基本Supabase操作hook
  │   │   └── useSupabaseRealtime.ts   // 實時數據訂閱hook
  │   ├── services/
  │   │   └── supabaseService.ts       // Supabase服務包裝器
  │   ├── components/
  │   │   └── supabase-test/           // Supabase測試與演示組件
  │   └── tstype.ts                    // 自動生成的TypeScript類型定義
  ├── .env.local                       // 本地環境變數（不提交到git）
  ├── .env.production                  // 生產環境變數模板
  ├── SUPABASE_SETUP.md                // Supabase設置指南
  ├── SUPABASE_REALTIME.md             // Supabase實時功能指南
  └── SUPABASE_TYPES.md                // TypeScript類型管理指南
```

## 文檔

專案包含以下Supabase相關文檔：

1. **SUPABASE_SETUP.md** - 基本設置和使用指南
2. **SUPABASE_REALTIME.md** - 實時功能實現與最佳實踐
3. **SUPABASE_TYPES.md** - TypeScript類型生成與管理

請參閱這些文檔以獲取每個主題的詳細信息。

## 示例與使用方法

### 基本CRUD操作

使用`useSupabase` hook進行基本的CRUD操作：

```typescript
import useSupabase from '../hooks/useSupabase';
import type { Database } from '../tstype';

type BreedRecord = Database['public']['Tables']['breedrecordorm']['Row'];

function MyComponent() {
  const {
    data: records,
    loading,
    error,
    insert,
    update,
    remove,
    refetch
  } = useSupabase<BreedRecord>('breedrecordorm');

  // 獲取記錄（自動在組件掛載時獲取）
  // 記錄將存儲在records變數中

  // 添加新記錄
  const addRecord = async () => {
    await insert({
      farm_name: '測試農場',
      chicken_breed: '黑羽雞',
      breed_date: '2023-01-01',
      breed_male: 10,
      breed_female: 100,
      is_completed: false
    });
  };

  // 更新記錄
  const updateRecord = async (id: string) => {
    await update(id, { is_completed: true });
  };

  // 刪除記錄
  const deleteRecord = async (id: string) => {
    await remove(id);
  };

  // 手動刷新數據
  const refreshData = () => {
    refetch();
  };

  return (
    // 組件UI
  );
}
```

### 實時數據訂閱

使用`useSupabaseRealtime` hook監聽資料變更：

```typescript
import useSupabaseRealtime from '../hooks/useSupabaseRealtime';
import SupabaseService from '../services/supabaseService';
import type { Database } from '../tstype';

type BreedRecord = Database['public']['Tables']['breedrecordorm']['Row'];

function RealtimeComponent() {
  const {
    data: records,
    loading,
    error,
    refetch,
    realtimeEnabled,
    setRealtimeEnabled
  } = useSupabaseRealtime<BreedRecord>(
    'breedrecordorm',
    SupabaseService.getAllBreedRecords,
    { autoRefresh: true } // 可選，設置為false以禁用自動刷新
  );

  // 開關實時更新
  const toggleRealtime = () => {
    setRealtimeEnabled(!realtimeEnabled);
  };

  return (
    // 組件UI
  );
}
```

### 使用SupabaseService

對於更複雜的操作，可以使用`SupabaseService`：

```typescript
import SupabaseService from '../services/supabaseService';

async function fetchBreedingStatistics() {
  try {
    // 獲取按農場分組的養殖統計數據
    const farmStats = await SupabaseService.getBreedingStatsByFarm();
    
    // 使用結果
    console.log('Farm Statistics:', farmStats);
    
    return farmStats;
  } catch (error) {
    console.error('Error fetching statistics:', error);
    throw error;
  }
}
```

## 測試

### 測試網頁

專案包含一個Supabase測試頁面，可以在開發過程中用來測試與Supabase的連接和基本功能：

1. 啟動開發服務器：
   ```bash
   bun run dev
   ```

2. 在瀏覽器打開應用，並導航到`#supabase-test`頁面。

3. 測試頁面提供了以下功能：
   - 顯示Supabase連接狀態
   - 基本的CRUD操作示例
   - 實時數據訂閱演示
   - 標準hook與實時hook的對比

### 自動化測試

要添加與Supabase相關的自動化測試，建議使用以下方法：

1. **模擬Supabase客戶端**：為測試創建一個模擬的Supabase客戶端
2. **測試Hooks**：測試自定義hook的行為
3. **組件測試**：測試使用Supabase數據的組件

## 部署

當部署使用Supabase的應用時，請確保：

1. **環境變數**：設置正確的Supabase URL和匿名金鑰
2. **CORS配置**：在Supabase中配置允許的來源
3. **行級安全性（RLS）**：設置適當的資料庫訪問策略

### 部署檢查清單

- [ ] Supabase專案設置完成
- [ ] 環境變數已配置
- [ ] CORS設置允許生產域名訪問
- [ ] 資料庫表已創建並配置了RLS策略
- [ ] 類型定義已更新

## 常見問題

### Supabase連接問題

**問題：** 無法連接到Supabase服務器
**解決方案：**
- 檢查環境變數是否正確設置
- 確認Supabase專案是否在線
- 檢查CORS配置是否允許您的域名

### 類型錯誤

**問題：** TypeScript報告類型不匹配錯誤
**解決方案：**
- 重新生成或更新類型定義文件
- 確保您使用了正確的導入路徑
- 檢查資料庫結構是否與類型定義匹配

### 實時更新不工作

**問題：** 實時更新不觸發或不工作
**解決方案：**
- 確認您已啟用realtimeEnabled
- 檢查Supabase專案實時功能是否啟用
- 添加調試日誌來查看實時事件是否觸發

### 性能問題

**問題：** 大量數據導致性能問題
**解決方案：**
- 使用分頁和過濾來減少加載的數據量
- 限制實時訂閱的範圍
- 考慮使用更高級的緩存策略

## 貢獻

在向專案添加更多Supabase功能或更改時，請遵循以下準則：

1. 創建一個短期功能分支
2. 確保更新相關文檔
3. 更新任何受影響的TypeScript類型
4. 撰寫測試覆蓋新功能
5. 使用拉取請求流程

## 資源

- [Supabase官方文檔](https://supabase.io/docs)
- [Supabase JavaScript客戶端](https://github.com/supabase/supabase-js)
- [Supabase社區](https://github.com/supabase/supabase/discussions)
