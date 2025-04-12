# Supabase TypeScript 類型生成與管理指南

本文檔說明如何在CleanSales前端專案中生成和管理Supabase資料庫的TypeScript類型定義。

## 類型定義的重要性

使用強類型在前端開發中有以下好處：

1. **編譯時類型檢查**: 在編譯時捕獲類型相關錯誤，減少運行時錯誤。
2. **代碼自動完成**: 編輯器可以提供準確的自動完成建議，提高開發效率。
3. **資料結構文檔**: 類型定義作為文檔，幫助開發人員了解資料庫結構。
4. **重構安全性**: 當資料庫結構變更時，TypeScript編譯器會標示所有需要更新的代碼。

## 生成類型定義

Supabase提供了多種方式生成TypeScript類型定義：

### 方法1: 使用Supabase CLI

1. 安裝Supabase CLI:
   ```bash
   npm install -g supabase
   ```

2. 登入你的Supabase賬戶:
   ```bash
   supabase login
   ```

3. 生成類型定義:
   ```bash
   supabase gen types typescript --project-id your-project-id > src/tstype.ts
   ```

### 方法2: 使用Supabase管理控制台

1. 登入[Supabase管理控制台](https://app.supabase.io/)
2. 選擇你的專案
3. 導航到 Project Settings > API
4. 在"TypeScript定義"部分，點擊"Generate types"
5. 複製生成的類型定義
6. 粘貼到你的專案中的`src/tstype.ts`文件

### 方法3: 使用Supabase JavaScript客戶端(最新版)

最新版的Supabase JavaScript客戶端(v2.x+)支持通過API直接獲取類型定義：

```typescript
import { createClient } from '@supabase/supabase-js'

// 獲取類型定義
const supabase = createClient('YOUR_SUPABASE_URL', 'YOUR_SUPABASE_KEY')
const types = await supabase.api.getTypes()

// 保存到文件
// 需要使用Node.js fs模組或瀏覽器下載功能
```

## 自動化類型生成

為了確保前端類型定義與資料庫結構同步，我們可以設置自動化流程：

### 選項1: 使用Git Hooks

在pre-commit或pre-push hook中添加類型生成命令：

```bash
# .git/hooks/pre-push
#!/bin/sh

echo "Generating Supabase types..."
supabase gen types typescript --project-id your-project-id > src/tstype.ts
git add src/tstype.ts
```

### 選項2: 使用CI/CD流程

在CI/CD流程中添加類型生成步驟，例如在GitHub Actions中：

```yaml
# .github/workflows/update-types.yml
name: Update Supabase Types

on:
  schedule:
    - cron: '0 0 * * *'  # 每天運行
  workflow_dispatch:     # 允許手動觸發

jobs:
  update-types:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2

      - name: Setup Node.js
        uses: actions/setup-node@v2
        with:
          node-version: '18'

      - name: Install Supabase CLI
        run: npm install -g supabase

      - name: Login to Supabase
        run: supabase login --token ${{ secrets.SUPABASE_ACCESS_TOKEN }}

      - name: Generate types
        run: supabase gen types typescript --project-id ${{ secrets.SUPABASE_PROJECT_ID }} > src/tstype.ts

      - name: Commit and push if changed
        run: |
          git config --global user.name 'GitHub Actions'
          git config --global user.email 'actions@github.com'
          git add src/tstype.ts
          git commit -m "Update Supabase types" || exit 0
          git push
```

## 使用生成的類型

生成的類型定義文件(`tstype.ts`)包含了完整的資料庫結構定義。以下是使用這些類型的示例：

### 基本使用方法

```typescript
import { supabase } from '../utils/supabaseClient';
import type { Database } from '../tstype';

// 定義表格記錄類型
type BreedRecord = Database['public']['Tables']['breedrecordorm']['Row'];
type FeedRecord = Database['public']['Tables']['feedrecordorm']['Row'];
type SaleRecord = Database['public']['Tables']['salerecordorm']['Row'];

// 使用類型的函數
async function fetchBreedRecords(): Promise<BreedRecord[]> {
  const { data, error } = await supabase
    .from('breedrecordorm')
    .select('*');

  if (error) throw error;
  return data || [];
}
```

### React組件中使用

```typescript
import React, { useState, useEffect } from 'react';
import { supabase } from '../utils/supabaseClient';
import type { Database } from '../tstype';

type BreedRecord = Database['public']['Tables']['breedrecordorm']['Row'];

const BreedRecordsList: React.FC = () => {
  const [records, setRecords] = useState<BreedRecord[]>([]);

  useEffect(() => {
    // 獲取養殖記錄
    const fetchRecords = async () => {
      const { data, error } = await supabase
        .from('breedrecordorm')
        .select('*');

      if (!error && data) {
        setRecords(data);
      }
    };

    fetchRecords();
  }, []);

  return (
    <div>
      <h2>養殖記錄</h2>
      <ul>
        {records.map(record => (
          <li key={record.unique_id}>
            {record.farm_name} - {record.chicken_breed} ({record.breed_date})
          </li>
        ))}
      </ul>
    </div>
  );
};

export default BreedRecordsList;
```

## 處理資料庫變更

當資料庫結構變更時，需要重新生成類型定義：

1. 更新資料庫結構（添加/修改表格、欄位等）
2. 重新生成類型定義文件
3. 更新前端代碼以適應新的類型

TypeScript編譯器會標示所有需要更新的地方，這是強類型系統的主要優點之一。

## 最佳實踐

1. **版本控制**: 將生成的類型定義文件納入版本控制
2. **定期更新**: 定期更新類型定義以確保與資料庫結構同步
3. **使用部分類型**: 使用Typescript的`Pick`和`Omit`來創建更精確的子類型
4. **使用自定義類型**: 對於特殊情況，可以擴展生成的類型
5. **類型註解**: 在關鍵部分添加類型註解，提高代碼可讀性

## 示例：建立自定義類型

有時需要基於生成的類型創建自定義類型：

```typescript
import type { Database } from '../tstype';

// 基本記錄類型
type BreedRecord = Database['public']['Tables']['breedrecordorm']['Row'];

// 不含ID和更新時間的養殖記錄類型(用於新增記錄)
type NewBreedRecord = Omit<BreedRecord, 'unique_id' | 'updated_at'>;

// 只包含特定欄位的養殖記錄摘要類型
type BreedRecordSummary = Pick<BreedRecord, 'farm_name' | 'chicken_breed' | 'breed_date'>;

// 擴展類型添加計算屬性
interface EnhancedBreedRecord extends BreedRecord {
  totalChickens: number;
  malePercentage: number;
  femalePercentage: number;
}

// 建立擴展記錄的函數
function enhanceBreedRecord(record: BreedRecord): EnhancedBreedRecord {
  const totalChickens = record.breed_male + record.breed_female;
  return {
    ...record,
    totalChickens,
    malePercentage: (record.breed_male / totalChickens) * 100,
    femalePercentage: (record.breed_female / totalChickens) * 100
  };
}
```

## 處理特殊情況

### 聯合查詢

當使用Supabase的聯合查詢功能時，需要創建自定義類型來表示結果：

```typescript
import type { Database } from '../tstype';

type BreedRecord = Database['public']['Tables']['breedrecordorm']['Row'];
type FeedRecord = Database['public']['Tables']['feedrecordorm']['Row'];

// 定義聯合查詢結果類型
interface BreedingWithFeeds extends BreedRecord {
  feedrecordorm: FeedRecord[] | null;
}

// 使用聯合查詢
async function fetchBreedingWithFeeds(batchName: string): Promise<BreedingWithFeeds | null> {
  const { data, error } = await supabase
    .from('breedrecordorm')
    .select(`
      *,
      feedrecordorm:feedrecordorm(*)
    `)
    .eq('batch_name', batchName)
    .single();

  if (error) throw error;
  return data;
}
```

### JSON欄位

對於包含JSON數據的欄位，可以創建更具體的類型：

```typescript
import type { Database } from '../tstype';

type BatchCustomData = Database['public']['Tables']['batchcustomdata']['Row'];

// 為JSON內容定義明確的類型
interface CustomContent {
  notes: string;
  tags: string[];
  metadata: {
    source: string;
    version: number;
    lastUpdated: string;
  };
}

// 強類型的批次自定義數據
interface TypedBatchCustomData extends Omit<BatchCustomData, 'content'> {
  content: CustomContent;
}

// 使用強類型讀取JSON
async function getBatchCustomData(batchName: string): Promise<TypedBatchCustomData | null> {
  const { data, error } = await supabase
    .from('batchcustomdata')
    .select('*')
    .eq('batch_name', batchName)
    .single();

  if (error) throw error;
  if (!data) return null;

  return data as TypedBatchCustomData;
}
```

## 類型重用與共享

為了促進代碼復用，可以將常用類型定義提取到單獨的文件中：

```typescript
// src/types/supabase.ts
import type { Database } from '../tstype';

export type BreedRecord = Database['public']['Tables']['breedrecordorm']['Row'];
export type FeedRecord = Database['public']['Tables']['feedrecordorm']['Row'];
export type SaleRecord = Database['public']['Tables']['salerecordorm']['Row'];

export type NewBreedRecord = Omit<BreedRecord, 'unique_id' | 'updated_at'>;
export type NewFeedRecord = Omit<FeedRecord, 'unique_id' | 'updated_at'>;
export type NewSaleRecord = Omit<SaleRecord, 'unique_id' | 'updated_at'>;

// 可重用的聯合查詢類型
export interface BreedingWithFeeds extends BreedRecord {
  feedrecordorm: FeedRecord[] | null;
}
```

然後在組件和服務中導入這些類型：

```typescript
import { BreedRecord, NewBreedRecord } from '../types/supabase';
```

## 使用工具輔助生成類型

對於複雜的情況，可以使用zod或typebox等工具來定義和驗證類型：

```typescript
import { z } from 'zod';
import type { Database } from '../tstype';

type BreedRecord = Database['public']['Tables']['breedrecordorm']['Row'];

// 使用zod定義驗證模式
const BreedRecordSchema = z.object({
  unique_id: z.string(),
  breed_date: z.string(),
  breed_female: z.number().int().min(0),
  breed_male: z.number().int().min(0),
  chicken_breed: z.string(),
  farm_name: z.string(),
  is_completed: z.boolean(),
  updated_at: z.string()
});

// 新記錄模式
const NewBreedRecordSchema = BreedRecordSchema.omit({
  unique_id: true,
  updated_at: true
});

// 從zod生成類型
type ValidatedBreedRecord = z.infer<typeof BreedRecordSchema>;
type ValidatedNewBreedRecord = z.infer<typeof NewBreedRecordSchema>;

// 使用zod驗證數據
function createBreedRecord(data: unknown): Promise<BreedRecord> {
  // 驗證輸入數據
  const validatedData = NewBreedRecordSchema.parse(data);

  // 添加必要欄位
  const newRecord = {
    ...validatedData,
    unique_id: `breed-${Date.now()}`,
    updated_at: new Date().toISOString()
  };

  // 插入記錄
  return supabase
    .from('breedrecordorm')
    .insert(newRecord)
    .select()
    .single()
    .then(({ data, error }) => {
      if (error) throw error;
      if (!data) throw new Error('No data returned');
      return data;
    });
}
```

## 故障排除

### 類型不匹配錯誤

如果遇到類型不匹配錯誤，可以：

1. 確保類型定義是最新的
2. 檢查API返回的實際數據結構
3. 使用類型斷言進行臨時解決（但要謹慎使用）

### 處理可選字段

Supabase生成的類型通常已經包含了正確的可選字段標記，但有時可能需要手動調整：

```typescript
import type { Database } from '../tstype';

type BreedRecord = Database['public']['Tables']['breedrecordorm']['Row'];

// 手動調整部分欄位的可選性
interface AdjustedBreedRecord extends Omit<BreedRecord, 'farm_license' | 'sub_location'> {
  farm_license: string | null; // 確保這是可選的
  sub_location: string | null; // 確保這是可選的
}
```

## 結論

TypeScript類型定義是確保前端與Supabase資料庫良好集成的關鍵部分。通過定期生成和維護這些類型，可以大大提高開發效率和代碼質量。

在CleanSales專案中，我們將繼續使用這些最佳實踐來確保前端類型定義與資料庫結構保持同步。
