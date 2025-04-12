# Supabase 實時功能使用指南

本文檔說明如何在CleanSales前端專案中使用Supabase的實時功能來訂閱資料庫變更。

## 實時功能簡介

Supabase Realtime是一項強大的服務，可讓您的應用程序收到資料庫變更的即時通知。這對於需要即時反映數據變更的功能非常有用，例如：

- 即時顯示新增的記錄
- 當其他用戶修改資料時更新畫面
- 實時聊天或通知功能
- 共同編輯功能
- 多用戶儀表板

## 實現方式

在CleanSales專案中，我們通過`SupabaseService`中的`subscribeToTableChanges`方法提供了一個簡單的介面來使用這個功能。

### 基本用法

```typescript
import SupabaseService from '../services/supabaseService';

// 在組件中使用
function MyComponent() {
  useEffect(() => {
    // 訂閱養殖記錄表的變更
    const unsubscribe = SupabaseService.subscribeToTableChanges(
      'breedrecordorm',
      (payload) => {
        console.log('收到資料變更:', payload);
        
        // 根據事件類型處理不同情況
        const { eventType, new: newRecord, old: oldRecord } = payload;
        
        switch (eventType) {
          case 'INSERT':
            console.log('新增記錄:', newRecord);
            // 處理新增記錄的邏輯
            break;
            
          case 'UPDATE':
            console.log('更新記錄:', newRecord);
            console.log('原始記錄:', oldRecord);
            // 處理更新記錄的邏輯
            break;
            
          case 'DELETE':
            console.log('刪除記錄:', oldRecord);
            // 處理刪除記錄的邏輯
            break;
        }
      }
    );
    
    // 組件卸載時取消訂閱
    return () => {
      unsubscribe();
    };
  }, []);
  
  return (
    // 組件內容
  );
}
```

### 與React狀態整合

下面是如何將Supabase實時功能與React狀態整合的示例：

```typescript
import React, { useState, useEffect } from 'react';
import SupabaseService from '../services/supabaseService';
import type { Database } from '../tstype';

type BreedRecord = Database['public']['Tables']['breedrecordorm']['Row'];

function BreedingRecordsLiveView() {
  const [records, setRecords] = useState<BreedRecord[]>([]);
  const [loading, setLoading] = useState(true);
  
  // 初始加載資料
  useEffect(() => {
    const fetchInitialData = async () => {
      try {
        setLoading(true);
        const data = await SupabaseService.getAllBreedRecords();
        setRecords(data);
      } catch (error) {
        console.error('獲取資料失敗:', error);
      } finally {
        setLoading(false);
      }
    };
    
    fetchInitialData();
  }, []);
  
  // 訂閱實時更新
  useEffect(() => {
    const unsubscribe = SupabaseService.subscribeToTableChanges(
      'breedrecordorm',
      (payload) => {
        const { eventType, new: newRecord, old: oldRecord } = payload;
        
        setRecords(prevRecords => {
          switch (eventType) {
            case 'INSERT':
              // 將新記錄添加到列表頂部
              return [newRecord, ...prevRecords];
              
            case 'UPDATE':
              // 更新列表中的記錄
              return prevRecords.map(record => 
                record.unique_id === newRecord.unique_id ? newRecord : record
              );
              
            case 'DELETE':
              // 從列表中移除記錄
              return prevRecords.filter(record => 
                record.unique_id !== oldRecord.unique_id
              );
              
            default:
              return prevRecords;
          }
        });
      }
    );
    
    return () => {
      unsubscribe();
    };
  }, []);
  
  return (
    <div>
      <h2>實時養殖記錄</h2>
      {loading ? (
        <p>載入中...</p>
      ) : (
        <ul>
          {records.map(record => (
            <li key={record.unique_id}>
              {record.farm_name} - {record.chicken_breed} - {record.breed_date}
              {/* 更多資料顯示 */}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
```

## 實時功能的優化

### 使用自定義Hook

為了簡化實時功能的使用，我們可以創建一個自定義Hook：

```typescript
// hooks/useSupabaseRealtime.ts
import { useState, useEffect } from 'react';
import SupabaseService from '../services/supabaseService';

export function useSupabaseRealtime<T>(
  table: 'breedrecordorm' | 'feedrecordorm' | 'salerecordorm',
  initialFetchFunction: () => Promise<T[]>
) {
  const [data, setData] = useState<T[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  // 初始加載資料
  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        setError(null);
        const initialData = await initialFetchFunction();
        setData(initialData);
      } catch (err) {
        setError(err instanceof Error ? err : new Error(String(err)));
        console.error('獲取資料失敗:', err);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [initialFetchFunction]);

  // 訂閱實時更新
  useEffect(() => {
    const unsubscribe = SupabaseService.subscribeToTableChanges(
      table,
      (payload) => {
        const { eventType, new: newRecord, old: oldRecord } = payload;

        setData(prevData => {
          switch (eventType) {
            case 'INSERT':
              return [newRecord as T, ...prevData];

            case 'UPDATE':
              return prevData.map(item => 
                (item as any).unique_id === (newRecord as any).unique_id 
                  ? newRecord as T 
                  : item
              );

            case 'DELETE':
              return prevData.filter(item => 
                (item as any).unique_id !== (oldRecord as any).unique_id
              );

            default:
              return prevData;
          }
        });
      }
    );

    return () => {
      unsubscribe();
    };
  }, [table]);

  return { data, loading, error };
}
```

然後在您的組件中使用這個Hook：

```typescript
function BreedingRecordsView() {
  const { data: records, loading, error } = useSupabaseRealtime(
    'breedrecordorm',
    SupabaseService.getAllBreedRecords
  );
  
  if (loading) return <p>載入中...</p>;
  if (error) return <p>錯誤: {error.message}</p>;
  
  return (
    <div>
      <h2>養殖記錄 ({records.length})</h2>
      {/* 顯示記錄 */}
    </div>
  );
}
```

### 效能注意事項

使用實時功能時，請注意以下效能考慮：

1. **選擇性訂閱**: 只訂閱您真正需要實時更新的表格。
2. **篩選訂閱**: 如果可能，使用更精確的篩選條件來減少接收的更新數量。
3. **適當的卸載**: 確保在組件卸載時取消訂閱。
4. **狀態管理**: 考慮使用像Redux或Zustand這樣的全局狀態管理來處理實時更新。

## 進階用法

### 針對特定欄位的訂閱

```typescript
const subscription = supabase
  .channel('table-changes')
  .on(
    'postgres_changes',
    {
      event: '*',
      schema: 'public',
      table: 'breedrecordorm',
      filter: 'farm_name=eq.測試農場' // 只訂閱特定農場的記錄
    },
    callback
  )
  .subscribe();
```

### 訂閱特定事件

```typescript
const subscription = supabase
  .channel('specific-events')
  .on(
    'postgres_changes',
    {
      event: 'INSERT', // 只訂閱新增事件
      schema: 'public',
      table: 'salerecordorm'
    },
    insertCallback
  )
  .on(
    'postgres_changes',
    {
      event: 'UPDATE',
      schema: 'public',
      table: 'salerecordorm',
      filter: 'closed=eq.false' // 只訂閱未關閉記錄的更新
    },
    updateCallback
  )
  .subscribe();
```

## 故障排除

如果您在使用Supabase實時功能時遇到問題，請檢查以下幾點：

1. **確保實時功能已啟用**: 在Supabase儀表板中確認實時功能已啟用。
2. **檢查連接狀態**: 使用瀏覽器開發工具檢查WebSocket連接狀態。
3. **檢查資料庫觸發器**: 確保PostgreSQL觸發器正常工作。
4. **驗證權限**: 確保您有適當的權限策略來允許實時訂閱。

## 結論

Supabase實時功能為CleanSales前端應用程序提供了強大的實時數據同步能力。通過適當使用這些功能，我們可以創建更具響應性和協作性的用戶體驗。
