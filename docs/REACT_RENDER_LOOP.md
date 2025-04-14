# 解決React渲染迴圈問題

在開發CleanSales專案的Supabase整合時，我們遇到了標準Hook視圖出現渲染迴圈的問題。本文檔記錄了這個問題的原因和解決方案，以便未來參考。

## 問題描述

在使用useSupabase hook時，我們發現當執行數據操作（如insert、update、remove）後，組件會進入無限渲染迴圈，導致瀏覽器變得非常緩慢甚至崩潰。

主要症狀：
- 操作數據後，瀏覽器控制台顯示大量重複的網絡請求
- CPU使用率迅速上升
- 瀏覽器變得緩慢、無響應
- React DevTools顯示組件頻繁更新

## 問題原因

分析後，我們發現以下幾個導致渲染迴圈的因素：

1. **setState在回調中直接更新本地狀態**：在insert/update/delete操作之後，Hook中直接更新了本地狀態(setData)，導致組件重新渲染。

2. **useEffect依賴項中包含對象引用**：使用對象作為useEffect的依賴項，即使內容沒有變化，引用也會在每次渲染時改變，導致useEffect不斷觸發。

3. **缺少避免組件卸載後的狀態更新機制**：當組件卸載後，異步操作完成並嘗試更新狀態，會導致React警告和不穩定行為。

4. **查詢選項(options)在每次渲染時創建新實例**：即使內容相同，也會創建新的引用，觸發不必要的查詢和更新。

## 解決方案

我們採取了以下措施來解決渲染迴圈問題：

### 1. 使用isMounted Ref跟踪組件掛載狀態

```typescript
// 在hook頂部添加
const isMounted = useRef(true);

// 在useEffect中添加清理函數
useEffect(() => {
  return () => {
    isMounted.current = false;
  };
}, []);

// 在所有狀態更新前檢查組件是否仍然掛載
if (isMounted.current) {
  setData(result);
}
```

### 2. 使用字符串比較查詢選項變化

```typescript
// 使用ref儲存上一次選項的字符串表示
const lastOptionsString = useRef('');

// 檢查是否有實際變化
const optionsChanged = useCallback(() => {
  const currentOptionsString = JSON.stringify(options);
  if (currentOptionsString !== lastOptionsString.current) {
    lastOptionsString.current = currentOptionsString;
    return true;
  }
  return false;
}, [options]);

// 只在選項實際變化時才觸發查詢
useEffect(() => {
  if (autoFetch && optionsChanged()) {
    fetchData();
  }
}, [autoFetch, fetchData, optionsChanged]);
```

### 3. 避免在回調中直接更新本地狀態

修改CRUD操作，不直接更新本地狀態，而是重新獲取數據：

```typescript
// 插入/更新/刪除後不直接修改本地狀態
const insert = useCallback(async (record) => {
  // ...執行插入操作...
  
  // 不再直接更新本地狀態
  // setData(prev => [...prev, result]);
  
  // 而是重新獲取所有數據
  if (isMounted.current) {
    fetchData();
  }
}, [fetchData]);
```

### 4. 使用setTimeout解決可能的競態條件

在UI層面，我們在操作後添加了一個小延遲再刷新數據，避免可能的競態條件：

```typescript
// 組件中的事件處理函數
const handleSubmit = async (e) => {
  e.preventDefault();
  await insert(newRecord);
  
  // 添加延遲再刷新，避免競態條件
  setTimeout(() => refetch(), 300);
};
```

### 5. 優化狀態更新策略

在操作數據後使用專門的refetch方法，而不是直接操作本地狀態：

```typescript
// 將狀態更新集中到一個地方處理
const fetchData = useCallback(async () => {
  try {
    setLoading(true);
    const result = await queryData();
    if (isMounted.current) {
      setData(result);
      setError(null);
    }
  } catch (err) {
    if (isMounted.current) {
      setError(err);
    }
  } finally {
    if (isMounted.current) {
      setLoading(false);
    }
  }
}, [queryData]);
```

### 6. 使用useCallback包裝所有函數

確保所有的函數引用在渲染之間是穩定的：

```typescript
const handleDelete = useCallback((id) => {
  // ...刪除邏輯...
}, [dependencies]);
```

## 補充解決方案

### 使用React Query或SWR

對於更複雜的數據獲取和緩存需求，可以考慮使用專業庫：

```typescript
// 使用React Query
const { data, isLoading, error, refetch } = useQuery(
  ['table', options],
  fetchData,
  {
    staleTime: 10000,
    cacheTime: 15000
  }
);

// 或使用SWR
const { data, error, mutate } = useSWR(
  ['table', JSON.stringify(options)],
  fetchData
);
```

### 考慮useReducer代替多個useState

對於複雜的數據管理，使用useReducer可能比多個useState更易於管理：

```typescript
const [state, dispatch] = useReducer(reducer, {
  data: null,
  loading: false,
  error: null
});

// 在reducer中集中處理狀態更新
function reducer(state, action) {
  switch (action.type) {
    case 'FETCH_START':
      return { ...state, loading: true };
    case 'FETCH_SUCCESS':
      return { data: action.payload, loading: false, error: null };
    case 'FETCH_ERROR':
      return { ...state, loading: false, error: action.payload };
    default:
      return state;
  }
}
```

## 效能監測與調試

在解決渲染迴圈問題時，以下工具很有幫助：

1. **React DevTools Profiler**：識別過度渲染的組件
2. **Chrome Performance 面板**：分析CPU使用和幀率問題
3. **為組件添加console日誌**：跟踪渲染次數

```jsx
// 監測渲染次數
useEffect(() => {
  console.log('Component rendered:', Date.now());
}, []);

// 或使用自定義Hook
function useTraceUpdate(props) {
  const prev = useRef(props);
  useEffect(() => {
    const changedProps = Object.entries(props).reduce((ps, [k, v]) => {
      if (prev.current[k] !== v) {
        ps[k] = [prev.current[k], v];
      }
      return ps;
    }, {});
    if (Object.keys(changedProps).length > 0) {
      console.log('Changed props:', changedProps);
    }
    prev.current = props;
  });
}
```

## 最佳實踐總結

為避免React應用中的渲染迴圈問題，請遵循以下最佳實踐：

1. **使用純組件和memo**：避免不必要的重新渲染
2. **穩定函數引用**：始終使用useCallback包裝事件處理函數
3. **跟踪組件掛載狀態**：避免在組件卸載後更新狀態
4. **緩存複雜計算**：使用useMemo避免重複計算
5. **深度比較依賴項**：必要時使用深度比較而非引用比較
6. **批量狀態更新**：將相關狀態更新組合在一起
7. **優化useEffect觸發**：仔細檢查依賴項列表
8. **添加延遲機制**：在快速狀態變更時添加防抖或節流

通過遵循這些實踐，我們成功解決了CleanSales專案中的渲染迴圈問題，大幅提升了使用者體驗和應用性能。
