/**
 * 日期相關工具函數
 * 使用 date-fns 套件簡化日期計算和轉換邏輯
 */
import {
  format,
  parseISO,
  isValid,
  startOfDay,
  differenceInDays,
} from "date-fns";
import { WeekAge } from "@app-types";

/**
 * 格式化日期字符串為 YYYY-MM-DD 格式
 *
 * @param dateString - 要格式化的日期字符串，可能包含時間部分
 * @param fallback - 當輸入無效時的預設值
 * @returns 格式化後的日期字符串
 */
export function formatDate(dateString?: string | null, fallback = "-"): string {
  if (!dateString) return fallback;

  try {
    // 嘗試將字符串轉換為 Date 對象
    const date = parseISO(dateString);

    // 檢查日期是否有效
    if (!isValid(date)) return fallback;

    // 使用 date-fns 的 format 函數格式化日期
    return format(date, "yyyy-MM-dd");
  } catch {
    return fallback;
  }
}

/**
 * 計算日齡
 *
 * 計算從養殖日期到指定日期的天數差異
 *
 * @param breedDate - 養殖開始日期（字符串格式）
 * @param diffDate - 計算日齡的目標日期，默認為當前日期
 * @returns 日齡天數（包含起始日，所以加 1）
 */
export function calculateDayAge(
  breedDate: string,
  diffDate: Date = new Date()
): number {
  // 使用 date-fns 的 parseISO 和 startOfDay 函數處理日期
  const breedDateObj = startOfDay(parseISO(breedDate));
  const diffDateObj = startOfDay(diffDate);

  // 使用 date-fns 的 differenceInDays 函數計算天數差異
  const days = differenceInDays(diffDateObj, breedDateObj);

  // 包含起始日，所以加 1
  return days + 1;
}

/**
 * 計算週齡
 *
 * @param dayAge - 日齡天數
 * @returns 週齡，包含週數和天數
 */
export function calculateWeekAge(dayAge: number): WeekAge {
  // 對應餘數的天數映射表
  const DAY_MAPPING: ReadonlyArray<number> = [7, 1, 2, 3, 4, 5, 6] as const;

  // 計算週數
  const weekNumber =
    dayAge % 7 === 0 ? Math.floor(dayAge / 7) - 1 : Math.floor(dayAge / 7);

  // 計算天數
  const dayNumber = DAY_MAPPING[dayAge % 7];

  return { week: weekNumber, day: dayNumber };
}
