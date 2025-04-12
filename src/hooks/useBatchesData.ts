import { useState, useCallback } from "react";
import { useQuery } from "@tanstack/react-query";
import supabase from "@app-lib/supabaseClient";
import {
  ChickenBreedType,
  BreedRecordRow, // 飼養紀錄類型
} from "@app-types";
import { QueryOptions } from "@hooks/supabase/types"; // 移除 TableName
import { buildQuery } from "@hooks/supabase/queryBuilder";

// 移除了不再使用的 fetchAndGroupDataInChunks 輔助函數

/**
 * Custom Hook: **僅**用於根據過濾條件取得飼養紀錄 (breedrecordorm) 並分組
 */
export const useBatchesData = () => {
  // State: 選中的雞種過濾條件
  const [selectedBreed, setSelectedBreed] = useState<ChickenBreedType | null>(
    null
  );
  // State: 是否顯示已完成批次的過濾條件
  const [isCompleted, setIsCompleted] = useState<boolean>(false);

  // useCallback: 取得飼養紀錄的核心函數
  const fetchBreeds = useCallback(async () => {
    // 建立取得飼養紀錄的查詢選項
    const queryOptions: QueryOptions = {
      eq: {
        event: "ADDED",
        is_completed: isCompleted,
        ...(selectedBreed ? { chicken_breed: selectedBreed } : {}),
      },
      neq: {
        batch_name: null,
      },
    };
    try {
      // 執行查詢
      const query = buildQuery(supabase, "breedrecordorm", queryOptions);
      const { data, count, error } = await query;

      if (error) throw error;

      // 將飼養紀錄按批次名稱分組 (純函數版本)
      const groupedData = ((data as BreedRecordRow[]) || []).reduce<{
        [batchName: string]: BreedRecordRow[];
      }>((acc, record) => {
        const batchName = record.batch_name;
        if (!batchName) {
          return acc;
        }
        return {
          ...acc,
          [batchName]: [...(acc[batchName] || []), record],
        };
      }, {});

      const batchNames = Object.keys(groupedData); // 取得所有批次的名稱

      // **只回傳** 分組後的飼養紀錄、批次名稱列表及總數
      return {
        groupedBreeds: groupedData,
        batchNames: batchNames,
        count: count || 0,
      };
    } catch (error) {
      console.error("取得飼養資料時發生錯誤:", error);
      throw error;
    }
  }, [selectedBreed, isCompleted]);

  // 使用 React Query 執行飼養紀錄的資料取得
  const {
    data: breedsData, // 重新命名回傳的 data
    isLoading: breedsLoading, // 重新命名 isLoading
    isError: breedsIsError, // 重新命名 isError
    error: breedsError, // 重新命名 error
  } = useQuery({
    queryKey: ["breeds", selectedBreed, isCompleted],
    queryFn: fetchBreeds,
    // 可選：設定 staleTime 或 cacheTime
    // staleTime: 5 * 60 * 1000, // 5 分鐘內視為新鮮資料
  });

  // 處理雞種選擇變更的函數
  const handleBreedChange = (breed: ChickenBreedType) => {
    // 若再次點擊相同雞種，則取消選取 (設為 null)，否則設為選中的雞種
    setSelectedBreed((prevBreed) => (prevBreed === breed ? null : breed));
  };

  // 切換是否顯示已完成批次的函數
  const toggleIsCompleted = () => {
    setIsCompleted((prev) => !prev); // 切換布林值
  };

  // 回傳 Hook 的狀態與處理函數
  return {
    // 回傳 Hook 的狀態與處理函數 (只包含與飼養紀錄相關的部分)
    breedsData, // 分組後的飼養紀錄、批次名稱列表、總數
    breedsLoading,
    breedsIsError,
    breedsError,
    selectedBreed,
    handleBreedChange,
    isCompleted,
    toggleIsCompleted,
  };
};
