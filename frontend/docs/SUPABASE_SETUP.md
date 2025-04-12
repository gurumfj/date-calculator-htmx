# Supabase 整合指南

本文檔描述如何在 CleanSales 前端專案中設置和使用 Supabase。

## 目錄

1. [Supabase 簡介](#supabase-簡介)
2. [前置需求](#前置需求)
3. [設置步驟](#設置步驟)
4. [環境變數配置](#環境變數配置)
5. [Supabase 客戶端使用](#supabase-客戶端使用)
6. [資料庫類型生成](#資料庫類型生成)
7. [常見操作示例](#常見操作示例)
8. [測試頁面說明](#測試頁面說明)
9. [最佳實踐](#最佳實踐)
10. [故障排除](#故障排除)

## Supabase 簡介

Supabase 是一個開源的 Firebase 替代品，提供一整套後端服務，包括：

- PostgreSQL 資料庫
- 身份驗證服務
- 實時訂閱
- 存儲服務
- 邊緣函數
- 向量搜索

在本專案中，我們主要使用 Supabase 提供的資料庫功能。

## 前置需求

- Node.js 16+
- 一個 Supabase 專案 (可以在 [https://supabase.com](https://supabase.com) 免費創建)
- 您的 Supabase 專案 URL
- 您的 Supabase 匿名密鑰 (anon key)

## 設置步驟

1. 安裝 Supabase 客戶端庫：

   ```bash
   bun add @supabase/supabase-js
   ```

2. 創建 Supabase 客戶端配置文件：

   ```bash
   # 位置: src/utils/supabaseClient.ts
   ```

3. 設置環境變數：

   ```bash
   # 複製 .env.sample 到 .env.local（如果還沒有的話）
   cp .env.sample .env.local
   ```

4. 添加 Supabase 測試頁面：

   ```bash
   # 位置: src/components/supabase-test/SupabaseTest.tsx
   ```

5. 修改 App.tsx 以支持導航至 Supabase 測試頁面：

   ```bash
   # 修改 App.tsx 以包含 Supabase 測試路由
   ```

## 環境變數配置

在 `.env.local` 文件中添加以下環境變數：

```
VITE_SUPABASE_URL=YOUR_SUPABASE_URL
VITE_SUPABASE_ANON_KEY=YOUR_SUPABASE_ANON_KEY
```

替換 `YOUR_SUPABASE_URL` 和 `YOUR_SUPABASE_ANON_KEY` 為您的實際 Supabase 專案 URL 和匿名密鑰。

## Supabase 客戶端使用

使用 Supabase 客戶端的基本示例：

```typescript
import { supabase } from '../utils/supabaseClient';

// 獲取數據
const fetchData = async () => {
  const { data, error } = await supabase
    .from('your_table')
    .select('*');

  if (error) {
    console.error('Error fetching data:', error);
    return;
  }

  console.log('Data:', data);
};

// 插入數據
const insertData = async (newItem) => {
  const { data, error } = await supabase
    .from('your_table')
    .insert(newItem);

  if (error) {
    console.error('Error inserting data:', error);
    return;
  }

  console.log('Inserted data:', data);
};

// 更新數據
const updateData = async (id, updates) => {
  const { data, error } = await supabase
    .from('your_table')
    .update(updates)
    .eq('id', id);

  if (error) {
    console.error('Error updating data:', error);
    return;
  }

  console.log('Updated data:', data);
};

// 刪除數據
const deleteData = async (id) => {
  const { error } = await supabase
    .from('your_table')
    .delete()
    .eq('id', id);

  if (error) {
    console.error('Error deleting data:', error);
    return;
  }

  console.log('Data deleted successfully');
};
```

## 資料庫類型生成

本專案已經包含了生成的 TypeScript 類型定義，位於 `src/tstype.ts`。這些類型與 Supabase 資料庫結構對應，提供了良好的類型安全性。

如果您修改了資料庫結構，需要更新這些類型，您可以使用 Supabase CLI 重新生成它們：

1. 安裝 Supabase CLI：

   ```bash
   npm install -g supabase
   ```

2. 登錄您的 Supabase 帳戶：

   ```bash
   supabase login
   ```

3. 生成類型：

   ```bash
   supabase gen types typescript --project-id YOUR_PROJECT_ID > src/tstype.ts
   ```

## 常見操作示例

以下是一些在本專案中使用 Supabase 的常見操作示例：

### 養殖記錄操作

```typescript
// 導入類型
import { Database } from '../tstype';
type BreedRecord = Database['public']['Tables']['breedrecordorm']['Row'];

// 獲取養殖記錄
const fetchBreedRecords = async () => {
  const { data, error } = await supabase
    .from('breedrecordorm')
    .select('*')
    .order('breed_date', { ascending: false });

  if (error) throw error;
  return data as BreedRecord[];
};

// 根據農場名稱篩選
const fetchBreedRecordsByFarm = async (farmName: string) => {
  const { data, error } = await supabase
    .from('breedrecordorm')
    .select('*')
    .eq('farm_name', farmName);

  if (error) throw error;
  return data as BreedRecord[];
};

// 添加養殖記錄
const addBreedRecord = async (record: Omit<BreedRecord, 'unique_id' | 'updated_at'>) => {
  const newRecord = {
    ...record,
    unique_id: `breed-${Date.now()}`,
    updated_at: new Date().toISOString()
  };

  const { data, error } = await supabase
    .from('breedrecordorm')
    .insert(newRecord);

  if (error) throw error;
  return data;
};
```

### 飼料記錄操作

```typescript
// 導入類型
import { Database } from '../tstype';
type FeedRecord = Database['public']['Tables']['feedrecordorm']['Row'];

// 獲取特定批次的飼料記錄
const fetchFeedRecordsByBatch = async (batchName: string) => {
  const { data, error } = await supabase
    .from('feedrecordorm')
    .select('*')
    .eq('batch_name', batchName)
    .order('feed_date', { ascending: true });

  if (error) throw error;
  return data as FeedRecord[];
};
```

### 銷售記錄操作

```typescript
// 導入類型
import { Database } from '../tstype';
type SaleRecord = Database['public']['Tables']['salerecordorm']['Row'];

// 獲取未付款的銷售記錄
const fetchUnpaidSales = async () => {
  const { data, error } = await supabase
    .from('salerecordorm')
    .select('*')
    .eq('unpaid', true);

  if (error) throw error;
  return data as SaleRecord[];
};

// 更新銷售記錄為已付款
const markSaleAsPaid = async (uniqueId: string) => {
  const { error } = await supabase
    .from('salerecordorm')
    .update({
      unpaid: false,
      updated_at: new Date().toISOString()
    })
    .eq('unique_id', uniqueId);

  if (error) throw error;
  return true;
};
```

## 測試頁面說明

本專案包含一個 Supabase 測試頁面，用於展示和測試與 Supabase 的連接和基本 CRUD 操作。您可以通過點擊主應用頂部的 "Supabase 測試" 按鈕或在 URL 中添加 `#supabase-test` 來導航到測試頁面。

測試頁面包含以下功能：

1. 顯示 Supabase 連接狀態
2. 選項卡切換不同類型的記錄（養殖、飼料、銷售）
3. 添加測試養殖記錄的按鈕
4. 刷新數據的按鈕
5. 養殖記錄的表格顯示
6. 更新和刪除養殖記錄的操作按鈕

使用此頁面可以確認 Supabase 配置是否正確，並測試各種數據操作。

## 最佳實踐

使用 Supabase 時，請遵循以下最佳實踐：

1. **使用環境變數**：不要在代碼中硬編碼 Supabase URL 和密鑰，始終使用環境變數。

2. **類型安全**：利用生成的 TypeScript 類型，使您的代碼更加安全可靠。

3. **錯誤處理**：始終檢查並處理 Supabase 操作返回的錯誤。

4. **批量操作**：當需要插入或更新多條記錄時，使用批量操作而不是多次單獨操作。

5. **使用查詢過濾**：在服務端過濾數據，而不是獲取所有數據後在客戶端過濾。

6. **使用事務**：對於需要保持一致性的多步操作，使用 Supabase 的事務功能。

7. **行級安全（RLS）**：在 Supabase 專案中配置行級安全策略，以保護您的數據。

## 故障排除

遇到問題時，請檢查以下幾點：

1. **環境變數**：確保 `.env.local` 文件中的 Supabase URL 和密鑰正確。

2. **網絡連接**：���保您的應用可以連接到 Supabase 服務器。

3. **控制台錯誤**：查看瀏覽器開發者工具的控制台，了解任何 JavaScript 錯誤。

4. **Supabase 日誌**：查看 Supabase 儀表板中的日誌，了解服務端錯誤。

5. **類型錯誤**：如果遇到類型相關錯誤，確保您使用的是最新的類型定義，並正確引用它們。

6. **CORS 問題**：如果遇到 CORS 錯誤，確保您的 Supabase 專案配置允許來自您應用的請求。

7. **權限問題**：確保您的數據庫表有適當的權限策略，允許進行您嘗試的操作。

常見錯誤：

- `Error: The resource was not found` - 表名可能拼寫錯誤或不存在
- `Error: Permission denied` - 可能缺少適當的 RLS 策略
- `Error: Duplicate key value violates unique constraint` - 嘗試插入具有重複唯一鍵的記錄

如果您遇到其他問題，請參考 [Supabase 官方文檔](https://supabase.io/docs) 或在專案 Issues 中尋求幫助。
