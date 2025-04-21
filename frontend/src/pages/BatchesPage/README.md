# BatchesPage 模組

## 架構說明

本模組採用功能模組化設計，將批次管理頁面相關的所有組件、hooks、store和類型定義組織在一起。這種結構提供了更好的封裝性和可維護性。

### 目錄結構

```
BatchesPage/
├── index.tsx                # 主頁面組件
├── components/              # 頁面專用組件
│   ├── index.ts             # 導出所有組件的 barrel 文件
│   ├── BatchCard.tsx        # 批次卡片組件
│   ├── BatchFilters.tsx     # 批次篩選條件組件
│   └── BatchDetailPanel/    # 批次詳情面板（複合組件）
├── hooks/                   # 頁面專用的自定義 hooks
│   ├── index.ts             # 導出所有 hooks 的 barrel 文件
│   └── useFetchBatches.ts   # 批次資料獲取 hook
├── store/                   # 狀態管理
│   └── useBatchStore.ts     # Zustand store
└── types.ts                 # 頁面專用類型定義
```

### 主要組件

- `index.tsx`: 批次管理主頁面，整合所有子組件
- `components/BatchCard.tsx`: 展示單個批次的基本信息
- `components/BatchFilters.tsx`: 提供批次篩選功能
- `components/BatchDetailPanel/`: 顯示選中批次的詳細資訊

### 狀態管理

- `store/useBatchStore.ts`: 使用 Zustand 管理批次數據和 UI 狀態

### 數據獲取

- `hooks/useFetchBatches.ts`: 使用 React Query 實現批次數據的獲取和緩存

## 使用方式

```tsx
import BatchesPage from '@/pages/BatchesPage';

// 在路由中使用
<Route path="/batches" element={<BatchesPage />} />
```

## 設計理念

- **功能模組化**: 將相關代碼組織在一起，提高可維護性
- **清晰的職責分離**: 每個組件和 hook 都有明確的單一職責
- **一致的導入方式**: 使用 barrel 文件簡化導入語句
- **封裝內部實現**: 只暴露必要的 API，隱藏實現細節

## 擴展指南

新增功能時，請遵循以下原則：
1. 特定於此頁面的組件放在 `components/` 目錄
2. 共用組件應提升到應用級別的 `@/components/` 目錄
3. 保持 `index.tsx` 簡潔，主要作為組合各組件的容器
4. 在適當的 barrel 文件中導出新增的組件或 hooks
