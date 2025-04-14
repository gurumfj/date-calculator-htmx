import { Database } from "./database.types";
// 批次狀態列舉
export type BatchState = "breeding" | "sale" | "completed";

export type BreedRecordRow =
  Database["public"]["Tables"]["breedrecordorm"]["Row"];

export type FeedRecordRow =
  Database["public"]["Tables"]["feedrecordorm"]["Row"];

export type SaleRecordRow =
  Database["public"]["Tables"]["salerecordorm"]["Row"];

// BatchAggregate

export interface BatchAggregate {
  batchName: string;
  breeds: BreedRecordRow[];
  sales: SaleRecordRow[];
  feeds: FeedRecordRow[];
}
