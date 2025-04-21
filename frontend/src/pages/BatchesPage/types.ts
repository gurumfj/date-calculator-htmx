import { BatchActivity, ChickenBreedType } from "@app-types";

/**
 * 篩選設定介面
 * Why: 定義篩選設定的結構，方便後續擴展和維護。
 */
export type FilterSettings = {
  defaultDaysRange: number; // 預設查詢天數範圍，方便 UI 初始化時自動帶入
  defaultBreedSelected: ChickenBreedType; // 預設品種，通常為業務最常用的選項
  defaultActivity: BatchActivity[]; // 預設活動狀態，支援多選，方便複合查詢
  defaultSortOrder: "asc" | "desc"; // 預設排序方式，通常依照時間軸需求決定
};

// BatchFilters 代表 UI 當前的實際篩選狀態
// 欄位允許 null，代表使用者尚未選擇時的未定義狀態，提升彈性
// filterByActivity 為陣列，支援多重活動查詢，滿足複雜業務需求
export type BatchFilters = {
  filterByBreed: ChickenBreedType | null; // 可為 null，對應「全部品種」的情境
  filterByStart: Date | null; // 查詢起始日，null 代表不限
  filterByEnd: Date | null; // 查詢結束日，null 代表不限
  filterByActivity: BatchActivity[]; // 支援多選，方便複合查詢
  sortOrder: "asc" | "desc"; // 排序方式，與後端查詢一致
};
