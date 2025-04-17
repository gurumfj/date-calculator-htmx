import { create } from "zustand";
import { BatchAggregateIndex } from "@app-types";
import { BatchAggregateQuery } from "@/hooks/useBatchAggregateQueries";

const DEFAULT_QUERY: BatchAggregateQuery = {
  chickenBreed: "黑羽",
  start: (() => {
    const date = new Date();
    date.setDate(date.getDate() - 30);
    return date;
  })(),
  end: new Date(),
  sortOrder: "asc",
};

// 定義 store 的狀態類型
interface BatchState {
  // 批次索引資料
  queryParams: BatchAggregateQuery;
  batchIndices: BatchAggregateIndex[];
  selectedBatchName: string | null;

  // 操作方法
  setBatchIndices: (indices: BatchAggregateIndex[]) => void;
  setQueryParams: (params: BatchAggregateQuery) => void;
  setSelectedBatchName: (batchName: string | null) => void;

  // 重置方法
  resetQueryParams: () => void;
}

// 創建 store
export const useBatchStore = create<BatchState>((set) => ({
  queryParams: DEFAULT_QUERY,
  batchIndices: [],
  selectedBatchName: null,

  setBatchIndices: (indices) => set({ batchIndices: indices }),

  setQueryParams: (params) =>
    set({
      queryParams: {
        ...DEFAULT_QUERY,
        ...params,
      },
    }),

  setSelectedBatchName: (batchName) => set({ selectedBatchName: batchName }),

  resetQueryParams: () => set({ queryParams: DEFAULT_QUERY }),
}));
