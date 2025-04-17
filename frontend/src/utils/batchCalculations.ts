/**
 * 批次資料計算工具函數
 * 提供各種與批次相關的計算邏輯，用於前端渲染和數據處理
 */
import {
  BatchAggregate,
  BreedRecordRow,
  SaleRecordRow,
  FeedRecordRow,
  BatchActivity,
} from "@app-types";
import { calculateDayAge, calculateWeekAge } from "@utils/dateUtils";
import { WeekAge } from "@app-types";

/**
 * 計算批次的週齡範圍
 * @param batch 批次資料
 * @returns 包含最大和最小週齡的物件，如果只有一筆資料則最小週齡為null
 */
export function calculateBatchAgeRange(batch: BatchAggregate): {
  maxWeekAge: WeekAge;
  minWeekAge: WeekAge | null;
} {
  // 計算所有繁殖記錄的日齡
  const dayAges = batch.breeds.map((r: BreedRecordRow) =>
    calculateDayAge(r.breed_date, new Date())
  );

  // 計算最大週齡
  const maxWeekAge =
    dayAges.length > 0
      ? calculateWeekAge(Math.max(...dayAges))
      : { week: 0, day: 0 };

  // 計算最小週齡 (如果只有一筆資料則為null)
  const minWeekAge =
    dayAges.length > 1 ? calculateWeekAge(Math.min(...dayAges)) : null;

  return { maxWeekAge, minWeekAge };
}

/**
 * 計算批次的總雞數（公母雞總數）
 * @param batch 批次資料
 * @returns 包含公雞總數、母雞總數和總數的物件
 */
export function calculateTotalChickens(batch: BatchAggregate): {
  totalMale: number;
  totalFemale: number;
  totalBred: number;
} {
  // 計算公雞總數
  const totalMale = batch.breeds.reduce(
    (sum: number, r: BreedRecordRow) => sum + r.breed_male,
    0
  );

  // 計算母雞總數
  const totalFemale = batch.breeds.reduce(
    (sum: number, r: BreedRecordRow) => sum + r.breed_female,
    0
  );

  // 計算總數
  const totalBred = totalMale + totalFemale;

  return { totalMale, totalFemale, totalBred };
}

/**
 * 提取批次中的飼料製造商清單
 * @param batch 批次資料
 * @returns 逗號分隔的飼料製造商清單
 */
export function extractFeedManufacturers(batch: BatchAggregate): string {
  return Array.from(
    new Set(batch.feeds.map((f: FeedRecordRow) => f.feed_manufacturer))
  ).join(", ");
}

/**
 * 確定批次的當前活動
 * @param batch 批次資料
 * @returns 批次活動（飼養中、銷售中或已完成）
 */
export function determineBatchActivity(batch: BatchAggregate): BatchActivity {
  return batch.batchIndex.data?.batchActivity || "breeding";
}

/**
 * 計算批次的銷售百分比
 * @param batch 批次資料
 * @returns 銷售百分比（0-1之間的數值）
 */
export function calculateSalesPercentage(batch: BatchAggregate): number {
  // 計算總計飼養雞數
  const { totalBred } = calculateTotalChickens(batch);

  // 計算已售出雞數
  const totalSold = batch.sales.reduce(
    (sum: number, s: SaleRecordRow) => sum + s.male_count + s.female_count,
    0
  );

  // 計算銷售百分比
  return totalBred > 0 ? totalSold / totalBred : 0;
}

/**
 * 生成批次週齡字符串，用於複製功能
 * @param batch 批次資料
 * @returns 批次週齡字符串
 */
export function generateWeekAgeString(batch: BatchAggregate): string {
  return batch.breeds
    .map((r: BreedRecordRow) => {
      const w = calculateWeekAge(calculateDayAge(r.breed_date, new Date()));
      return `[${w.week}.${w.day}]`;
    })
    .join(", ");
}

/**
 * 生成批次複製文本內容
 * @param batch 批次資料
 * @returns 格式化的複製文本
 */
export function generateBatchCopyText(batch: BatchAggregate): string {
  const localDateStr = new Date()
    .toLocaleDateString("zh-TW", {
      year: "numeric",
      month: "2-digit",
      day: "2-digit",
    })
    .replace(/\//g, "-");

  const weekAgeStr = generateWeekAgeString(batch);

  return `${batch.batchName || batch.batchIndex.batch_name}\n${localDateStr}${weekAgeStr}`;
}

/**
 * 獲取批次的狀態顯示信息，包括背景色、文字色和標籤
 * @param state 批次狀態
 * @returns 狀態顯示信息物件
 */
export function getBatchStateDisplay(state: BatchActivity): {
  bgClass: string;
  textClass: string;
  label: string;
} {
  const stateDisplay = {
    breeding: {
      bgClass: "bg-green-100",
      textClass: "text-green-700",
      label: "在養",
    },
    selling: {
      bgClass: "bg-blue-100",
      textClass: "text-blue-700",
      label: "銷售",
    },
    soldout: {
      bgClass: "bg-orange-100",
      textClass: "text-orange-700",
      label: "售罄",
    },
    completed: {
      bgClass: "bg-gray-100",
      textClass: "text-gray-700",
      label: "結場",
    },
  };

  return stateDisplay[state];
}

/**
 * 對批次的繁殖記錄按照日齡排序（從老到新或從新到老）
 * @param breeds 繁殖記錄數組
 * @param descending 是否按降序排序，默認為true（從老到新）
 * @returns 排序後的繁殖記錄數組
 */
export function sortBreedsByAge(
  breeds: BreedRecordRow[],
  descending = true
): BreedRecordRow[] {
  return [...breeds].sort((a, b) => {
    const ageA = calculateDayAge(a.breed_date, new Date());
    const ageB = calculateDayAge(b.breed_date, new Date());
    return descending ? ageB - ageA : ageA - ageB;
  });
}

/**
 * 計算銷售相關統計數據
 * @param batch 批次資料
 * @returns 包含各種銷售統計指標的物件
 */
export function calculateSalesStatistics(batch: BatchAggregate): {
  totalMale: number;
  totalFemale: number;
  totalSales: number;
  totalRevenue: number;
  avgPricePerWeight: number;
  salesPeriodDates: [Date | string, Date | string | null];
  salesDuration: number;
  totalTransactions: number;
  salesOpenCloseDayage: number[];
} {
  const { breeds, sales } = batch;

  // 計算總公雞銷售數量
  const totalMale = sales.reduce(
    (acc: number, sale: SaleRecordRow) => acc + sale.male_count,
    0
  );

  // 計算總母雞銷售數量
  const totalFemale = sales.reduce(
    (acc: number, sale: SaleRecordRow) => acc + sale.female_count,
    0
  );

  // 計算總銷售數量
  const totalSales = sales.reduce(
    (acc: number, sale: SaleRecordRow) =>
      acc + sale.male_count + sale.female_count,
    0
  );

  // 計算總收入
  const totalRevenue = sales.reduce(
    (acc: number, sale: SaleRecordRow) => acc + (sale.total_price || 0),
    0
  );

  // 計算平均每公斤價格
  const validSalesForAvg = sales.filter(
    (sale: SaleRecordRow) =>
      (sale.total_weight || 0) > 0 && (sale.total_price || 0) > 0
  );

  const avgPricePerWeight = validSalesForAvg.length
    ? validSalesForAvg.reduce(
        (acc: number, sale: SaleRecordRow) =>
          acc + (sale.total_price || 0) / (sale.total_weight || 0),
        0
      ) / validSalesForAvg.length
    : 0;

  // 計算銷售週期
  const salesDates = sales.map((sale) => new Date(sale.sale_date));
  const sortedDates = [...salesDates].sort((a, b) => a.getTime() - b.getTime());

  const salesPeriodDates: [Date | string, Date | string | null] =
    sales.length > 0
      ? [sortedDates[0], sortedDates[sortedDates.length - 1]]
      : ["", null];

  // 計算銷售持續天數
  const salesDuration =
    sales.length > 1
      ? ((salesPeriodDates[1] as Date).getTime() -
          (salesPeriodDates[0] as Date).getTime()) /
          (1000 * 60 * 60 * 24) +
        1
      : 0;

  // 計算交易次數
  const totalTransactions = sales.length;

  // 計算銷售開始和結束的日齡
  const salesOpenCloseDayage = (): number[] => {
    if (!breeds.length || !sales.length) return [0, 0];

    const breedDate = new Date(breeds[0].breed_date);
    const firstSaleDate = sortedDates[0];
    const lastSaleDate = sortedDates[sortedDates.length - 1];

    const openDayage = Math.floor(
      (firstSaleDate.getTime() - breedDate.getTime()) / (1000 * 60 * 60 * 24)
    );

    const closeDayage = Math.floor(
      (lastSaleDate.getTime() - breedDate.getTime()) / (1000 * 60 * 60 * 24)
    );

    return [openDayage, closeDayage];
  };

  return {
    totalMale,
    totalFemale,
    totalSales,
    totalRevenue,
    avgPricePerWeight,
    salesPeriodDates,
    salesDuration,
    totalTransactions,
    salesOpenCloseDayage: salesOpenCloseDayage(),
  };
}

/**
 * 計算銷售紀錄的平均重量
 * @param breeds 繁殖記錄
 * @param sale 銷售紀錄
 * @returns 包含平均公雞重量和平均母雞重量的物件
 */
export const calculateSaleRecord = (
  breeds: BreedRecordRow[],
  sale: SaleRecordRow
) => {
  const dayAge = breeds.map((b) =>
    calculateDayAge(b.breed_date, new Date(sale.sale_date))
  );
  const baseWeight = () => {
    if (sale.total_weight) {
      return (
        (sale.total_weight - sale.male_count * 0.8) /
        (sale.male_count + sale.female_count)
      );
    }
    return 0;
  };
  const avgMaleWeight = sale.male_count > 0 ? baseWeight() + 0.8 : null;
  const avgFemaleWeight = sale.female_count > 0 ? baseWeight() : null;
  return {
    ...sale,
    dayAge,
    avgMaleWeight,
    avgFemaleWeight,
  };
};

/**
 * 計算批次的所有聚合數據
 * @param batch 批次資料
 * @returns 包含所有計算結果的綜合物件
 */
export function calculateBatchAggregate(batch: BatchAggregate): {
  ageRange: { maxWeekAge: WeekAge; minWeekAge: WeekAge | null };
  chickens: { totalMale: number; totalFemale: number; totalBred: number };
  feedManufacturers: string;
  batchActivity: BatchActivity;
  salesPercentage: number;
  salesStats: ReturnType<typeof calculateSalesStatistics>;
  saleRecords: ReturnType<typeof calculateSaleRecord>[];
} {
  return {
    ageRange: calculateBatchAgeRange(batch),
    chickens: calculateTotalChickens(batch),
    feedManufacturers: extractFeedManufacturers(batch),
    batchActivity: determineBatchActivity(batch),
    salesPercentage: calculateSalesPercentage(batch),
    salesStats: calculateSalesStatistics(batch),
    saleRecords: batch.sales.map((sale) =>
      calculateSaleRecord(batch.breeds, sale)
    ),
  };
}
