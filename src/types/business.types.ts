import { Database } from "./database.types";
// 批次活動列舉
export type BatchActivity = "breeding" | "selling" | "soldout" | "completed";

// 批次狀態列舉
export type BatchState = "breeding" | "sale" | "completed";

export const BatchActivityOptions = [
  { value: "breeding", label: "繁殖" },
  { value: "selling", label: "銷售" },
  { value: "soldout", label: "完售" },
  { value: "completed", label: "完成" },
];

export type BatchAggregateIndex =
  Database["public"]["Tables"]["batchaggregates"]["Row"];

export type BreedRecordRow =
  Database["public"]["Tables"]["breedrecordorm"]["Row"];

export type FeedRecordRow =
  Database["public"]["Tables"]["feedrecordorm"]["Row"];

export type SaleRecordRow =
  Database["public"]["Tables"]["salerecordorm"]["Row"];

// BatchAggregate
export interface BatchAggregate {
  batchIndex: BatchAggregateIndex;
  customData: CustomData;
  breeds: BreedRecordRow[];
  sales: SaleRecordRow[];
  feeds: FeedRecordRow[];
  batchName?: string; // 添加可選的 batchName 屬性，兼容舊代碼
}

export interface CustomData {
  batchActivity: BatchActivity;
}
