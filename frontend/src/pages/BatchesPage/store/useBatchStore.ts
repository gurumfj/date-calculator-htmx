import { BatchAggregateIndex } from "@/types";
import { BatchFilters, FilterSettings } from "../types";
import { create, StateCreator } from "zustand";
import { persist, createJSONStorage } from "zustand/middleware";

// 將預設篩選條件集中管理，方便日後調整與維護
// defaultDaysRange 設為 30 天，主要考量用戶最常查詢近一個月資料，兼顧效能與需求
const DEFAULT_FILTERS_SETTINGS: FilterSettings = {
  defaultDaysRange: 30,
  defaultBreedSelected: "黑羽", // 黑羽為主要品種，提升初次體驗友善度
  defaultActivity: [], // 預設無活動篩選，避免初始畫面過於侷限
  defaultSortOrder: "asc", // 升冪排序，符合時間軸閱讀習慣
};

// 將篩選設定、查詢條件、資料與 UI 狀態分離，方便維護與擴展
// 這樣的結構讓每個 concern 獨立，減少耦合
// 若未來要支援多組件共用 store，可直接擴充

type BatchesFilterStore = {
  // 篩選設定，集中管理預設值，避免硬編碼分散
  filterSettings: FilterSettings;
  setFilterSettings: (settings: FilterSettings) => void;
  resetFilterSettings: () => void;

  // 查詢條件，維持單一來源，確保 UI 與資料一致
  filter: BatchFilters;
  setFilter: (filter: BatchFilters) => void;
  resetFilter: () => void;

  // 資料快取，減少重複 API 請求，提升效能
  batchIndice: BatchAggregateIndex[];
  setBatchIndice: (batchIndice: BatchAggregateIndex[]) => void;

  // UI 狀態，分離選擇狀態，避免多層 props 傳遞
  selectedBatchName: string | null;
  setSelectedBatchName: (batchName: string | null) => void;
};

export const createBatchFilterStore: StateCreator<BatchesFilterStore> = (
  set
) => {
  // 直接回歸預設值，狀態持久化交由 middleware 處理
  return {
    // settings
    filterSettings: DEFAULT_FILTERS_SETTINGS, // 預設值統一來源，避免多處重複
    setFilterSettings: (settings: FilterSettings) =>
      set({ filterSettings: settings }), // 允許動態調整預設條件，支援進階設定
    resetFilterSettings: () =>
      set({ filterSettings: DEFAULT_FILTERS_SETTINGS }), // 一鍵還原預設，方便用戶重設

    // filter
    filter: {
      filterByBreed: DEFAULT_FILTERS_SETTINGS.defaultBreedSelected, // 預設品種，降低用戶操作門檻
      filterByStart: new Date(
        new Date().setDate(
          new Date().getDate() - DEFAULT_FILTERS_SETTINGS.defaultDaysRange
        )
      ), // 預設起始日為 30 天前，兼顧查詢效率與實用性
      filterByEnd: new Date(), // 預設結束日為今日
      filterByActivity: DEFAULT_FILTERS_SETTINGS.defaultActivity || [], // 無初始活動篩選，避免誤導
      sortOrder: DEFAULT_FILTERS_SETTINGS.defaultSortOrder, // 預設升冪排序
    },
    setFilter: (filter: BatchFilters) => set({ filter }), // 統一 filter 更新，方便追蹤
    resetFilter: () => {
      // resetFilter 返回預設設定，確保用戶能快速回到初始狀態
      const resetFilter = {
        filterByBreed: DEFAULT_FILTERS_SETTINGS.defaultBreedSelected,
        filterByStart: new Date(
          new Date().setDate(
            new Date().getDate() - DEFAULT_FILTERS_SETTINGS.defaultDaysRange
          )
        ),
        filterByEnd: new Date(),
        filterByActivity: DEFAULT_FILTERS_SETTINGS.defaultActivity || [],
        sortOrder: DEFAULT_FILTERS_SETTINGS.defaultSortOrder,
      };
      set({ filter: resetFilter });
    },

    // data
    batchIndice: [], // 快取批次索引，避免重複撈取
    setBatchIndice: (batchIndice: BatchAggregateIndex[]) =>
      set({ batchIndice }), // 支援批次資料動態更新

    // UI selected
    selectedBatchName: null, // 分離 UI 狀態，避免資料與視覺耦合
    /**
     * 僅允許由 URL (useParams) 控制 selectedBatchName
     * 禁止在元件中直接調用 setSelectedBatchName，必須透過 URL 導航觸發狀態變更
     * Why: 保持單一來源原則，確保 UI 狀態與 URL 完全一致，避免副作用與同步問題
     */
    setSelectedBatchName: (batchName: string | null) =>
      set({ selectedBatchName: batchName }), // 僅允許 BatchPage 透過 useEffect 控制
  };
};

// 判斷字串是否可被正確轉換為有效 Date 物件
// Why: 利用 new Date(value) 並檢查 getTime()，可自動涵蓋多種標準格式，彈性更高
const isValidDateString = (value: any): value is string => {
  if (typeof value !== "string") return false;
  const date = new Date(value);
  // getTime() 回傳 NaN 代表無法正確轉換為日期
  return !isNaN(date.getTime());
};

// 將 store 實例化，統一由 useBatchStore 取得，方便全專案共用
// 使用 zustand persist middleware，將狀態持久化於 sessionStorage
export const useBatchStore = create<BatchesFilterStore>()(
  persist(createBatchFilterStore, {
    name: "batchStore", // sessionStorage 的 key 名稱，方便管理
    // 使用 createJSONStorage 自動處理序列化/反序列化，並指定 sessionStorage
    storage: createJSONStorage(() => sessionStorage, {
      // Why: JSON 會將 Date 物件序列化成字串，需在還原時轉回 Date
      // 這樣可以確保元件取得正確型別
      reviver: (key, value) => {
        // 僅針對 filter 物件中的日期欄位做處理
        // Why: 避免誤將一般字串轉成 Date，僅處理已知欄位
        if (
          (key === "filterByStart" || key === "filterByEnd") &&
          isValidDateString(value)
        ) {
          try {
            // Why: 將 ISO 字串還原為 Date，確保型別正確
            return new Date(value);
          } catch (e) {
            // Why: 若轉換失敗，回傳原值避免程式崩潰
            console.error(`還原日期失敗 key="${key}":`, value, e);
            return value;
          }
        }
        // Why: 其他欄位維持原樣
        return value;
      },
    }),
    // 僅同步必要欄位，避免快取資料過大與效能問題
    partialize: (state) => ({
      filter: state.filter,
    }),
  })
);
