import { Database } from "./database.types";

// 批次活動狀態以 union type 定義，確保型別安全並限制可用值
// 這樣設計可避免 typo，並方便型別自動提示與 refactor
export type BatchActivity = "breeding" | "selling" | "soldout" | "completed";

// CustomData 用於 batch 資料表中的自定義欄位
// 將 batchActivity 明確獨立，有助於狀態流轉與 UI 呈現
export interface CustomData {
  batchActivity: BatchActivity;
}

// 活動選項集中定義，方便前端 UI 直接引用，避免重複硬編碼
export const BatchActivityOptions = [
  { value: "breeding", label: "在養" },
  { value: "selling", label: "銷售" },
  { value: "soldout", label: "完售" },
  { value: "completed", label: "完成" },
];

// BatchAggregate 作為 BatchAggregateWithRows 的別名，維持舊代碼相容性
// 這樣設計可平滑過渡資料結構調整，減少 refactor 風險
export type BatchAggregate = BatchAggregateWithRows;

// 直接對應資料庫型別，確保前後端資料結構一致，提升維護性
export type BatchAggregateIndex =
  Database["public"]["Tables"]["batchaggregates"]["Row"];

type BreedRecordRow = Database["public"]["Tables"]["breedrecordorm"]["Row"];
type FeedRecordRow = Database["public"]["Tables"]["feedrecordorm"]["Row"];
export type SaleRecordRow =
  Database["public"]["Tables"]["salerecordorm"]["Row"];

// 將 index、各類紀錄以物件型別包裝，方便聚合與擴充
// 這樣設計可讓聚合型別靈活組合，支援未來增加新類型紀錄
// 批次索引對象
// Breed/Feed/SaleRecords 統一結構，方便消費與型別推斷
// BatchAggregateWithRows 為所有聚合資料的最終型別

type BatchIndex = {
  index: BatchAggregateIndex;
};

type BreedRecords = {
  breeds: BreedRecordRow[];
};

type FeedRecords = {
  feeds: FeedRecordRow[];
};

type SaleRecords = {
  sales: SaleRecordRow[];
};

// BatchAggregate 完整資料結構，聚合所有子型別，方便前端一次取得所有資料
export type BatchAggregateWithRows = BatchIndex &
  BreedRecords &
  FeedRecords &
  SaleRecords;
