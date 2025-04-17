/**
 * 系統中使用的常數和列舉類型
 */

// ===== 記錄事件相關常數 =====

/**
 * 記錄事件列舉
 */
export enum RecordEvent {
  Added = "ADDED",
  Deleted = "DELETED",
  Updated = "UPDATED",
}

/**
 * 記錄事件類型
 * 可用於類型註解，同時保持與資料庫字串類型相容
 */
export type RecordEventType = "ADDED" | "DELETED" | "UPDATED";

/**
 * 記錄事件列表
 */
export const RECORD_EVENTS: RecordEventType[] = ["ADDED", "DELETED", "UPDATED"];

/**
 * 記錄事件顯示名稱對映表
 */
export const RECORD_EVENT_DISPLAY_NAME: Record<RecordEventType, string> = {
  ADDED: "新增",
  DELETED: "刪除",
  UPDATED: "更新",
};

// ===== 雞隻品種相關常數 =====

/**
 * 雞隻品種列舉
 */
// export enum ChickenBreed {
//   BlackFeather = "黑羽",
//   Traditional = "古早",
//   SheBlack = "舍黑",
//   Capon = "閹雞",
// }

/**
 * 雞隻品種類型
 * 可用於類型註解，同時保持與資料庫字串類型相容
 */
export type ChickenBreedType = "黑羽" | "古早" | "舍黑" | "閹雞";

/**
 * 雞隻品種和顯示名稱的對映表
 */
export const CHICKEN_BREED_DISPLAY_NAME: Record<ChickenBreedType, string> = {
  黑羽: "黑羽雞",
  古早: "古早雞",
  舍黑: "舍黑雞",
  閹雞: "閹雞",
};

/**
 * 雞隻品種列表
 */
export const CHICKEN_BREEDS: ChickenBreedType[] = [
  "黑羽",
  "古早",
  "舍黑",
  "閹雞",
];

// ===== 批次活動顏色常數 =====

import { BatchActivity } from "./business.types";

/**
 * 批次活動對應的顏色
 * 提供每種批次狀態的背景色和懸停色
 */
export const BATCH_ACTIVITY_COLORS: Record<
  BatchActivity,
  { bg: string; hover: string }
> = {
  breeding: { bg: "#007AFF", hover: "#0067D6" }, // 飼養中 - 藍色
  selling: { bg: "#FF9500", hover: "#EB8A00" }, // 銷售中 - 橙色
  soldout: { bg: "#34C759", hover: "#2BA84C" }, // 已售罄 - 綠色
  completed: { bg: "#8E8E93", hover: "#7A7A80" }, // 已完成 - 灰色
};
