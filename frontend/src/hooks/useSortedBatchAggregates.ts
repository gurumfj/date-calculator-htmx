import { useMemo } from "react";
import { useBatchesData } from "./useBatchesData";
import { useBatchDetailsQueries } from "./useBatchDetailsQueries";
import { BatchAggregate } from "@app-types";

type SortOrder = "asc" | "desc";

/**
 * Custom Hook: 整合飼養、銷售、飼料資料，並根據指定順序排序。
 * @param sortOrder - 排序順序 ('asc' 或 'desc')
 * @returns 包含排序後的批次資料、載入狀態、錯誤狀態、總數及過濾相關狀態/函數的物件
 */
export const useSortedBatchAggregates = (sortOrder: SortOrder) => {
  // 1. 取得飼養資料及批次名稱
  const {
    breedsData,
    breedsLoading,
    breedsError,
    selectedBreed,
    handleBreedChange,
    isCompleted,
    toggleIsCompleted,
  } = useBatchesData();

  // 2. 根據批次名稱取得銷售和飼料資料
  const batchNames = breedsData?.batchNames || [];
  const { salesByBatch, feedsByBatch, isSubQueryLoading, subQueryError } =
    useBatchDetailsQueries(batchNames);

  // 3. 合併與排序資料
  const sortedBatches: (BatchAggregate & { latestDate: number })[] =
    useMemo(() => {
      const groupedBreeds = breedsData?.groupedBreeds;
      const currentBatchNames = breedsData?.batchNames;
      if (
        !groupedBreeds ||
        !currentBatchNames ||
        currentBatchNames.length === 0
      )
        return [];

      const combined = currentBatchNames
        .map((batchName) => {
          const breeds = groupedBreeds[batchName] || [];
          const sales = salesByBatch[batchName] || [];
          const feeds = feedsByBatch[batchName] || [];
          // 計算 latestDate (保持此邏輯用於排序)
          const latestDate = breeds.reduce((latest, record) => {
            const recordDate = record.breed_date
              ? new Date(record.breed_date).getTime()
              : 0;
            return Math.max(latest, isNaN(recordDate) ? 0 : recordDate);
          }, 0);
          return { batchName, breeds, sales, feeds, latestDate };
        })
        .filter((batch) => batch.breeds.length > 0);

      // 排序
      combined.sort((a, b) =>
        sortOrder === "asc"
          ? a.latestDate - b.latestDate
          : b.latestDate - a.latestDate
      );
      return combined;
    }, [breedsData, salesByBatch, feedsByBatch, sortOrder]);

  const batchesObject = useMemo(() => {
    return sortedBatches.reduce(
      (acc, batch) => {
        acc[batch.batchName] = batch;
        return acc;
      },
      {} as { [key: string]: BatchAggregate & { latestDate: number } }
    );
  }, [sortedBatches]);
  // 4. 處理整體載入與錯誤狀態
  const isLoading = breedsLoading || isSubQueryLoading;
  const error = breedsError || subQueryError;

  return {
    sortedBatches,
    batchesObject,
    isLoading,
    error,
    count: breedsData?.count || 0, // 從 breedsData 取得總數
    // 透傳過濾相關的狀態和函數
    selectedBreed,
    handleBreedChange,
    isCompleted,
    toggleIsCompleted,
  };
};
