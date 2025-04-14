import React, { useState, useMemo, useCallback } from "react";
import { useQuery, useQueries } from "@tanstack/react-query";
import supabase from "@app-lib/supabaseClient";
import { QueryOptions } from "@hooks/supabase/types";
import { buildQuery } from "@hooks/supabase/queryBuilder";
import {
  BatchAggregate,
  BreedRecordRow,
  SaleRecordRow,
  FeedRecordRow,
} from "@app-types";
import { ChickenBreedType } from "@app-types";

// 默認查詢選項
const DEFAULT_QUERY_OPTIONS: QueryOptions = {
  eq: {
    event: "ADDED",
  },
  neq: {
    batch_name: null,
  },
};

/**
 * 自定義Hook: 使用React Query獲取繁殖記錄及相關批次聚合數據
 */
export const useBreedRecordsWithAggregates = () => {
  // 查詢選項狀態
  const [queryOptions, setQueryOptions] = useState<QueryOptions>(
    DEFAULT_QUERY_OPTIONS
  );

  // 排序狀態
  const [sortColumn, setSortColumn] =
    useState<keyof BreedRecordRow>("breed_date");
  const [sortDirection, setSortDirection] = useState<"asc" | "desc">("asc");

  // 搜尋狀態
  const [searchTerm, setSearchTerm] = useState<string>("");

  // 使用React Query獲取繁殖記錄
  const {
    data: breedRecords,
    isLoading,
    error,
    refetch: fetchBreeds,
  } = useQuery<BreedRecordRow[], Error>({
    queryKey: ["breedRecords", { ...DEFAULT_QUERY_OPTIONS, ...queryOptions }],
    queryFn: async () => {
      const query = supabase.from("breedrecordorm").select("*");

      if (queryOptions.eq) {
        Object.entries(queryOptions.eq).forEach(([key, value]) => {
          query.eq(key, value);
        });
      }

      if (queryOptions.neq) {
        Object.entries(queryOptions.neq).forEach(([key, value]) => {
          query.neq(key, value);
        });
      }

      const { data } = await query;
      return data || [];
    },
  });

  // 獲取唯一批次名稱
  const batchNames = useMemo(() => {
    return breedRecords
      ? [...new Set(breedRecords.map((record) => record.batch_name))].filter(
          (name): name is string => name !== null
        )
      : [];
  }, [breedRecords]);

  // 使用useQueries並行獲取所有批次的銷售和飼料記錄
  const batchQueriesResults = useQueries({
    queries: batchNames
      .map((batchName) => [
        {
          queryKey: ["salesByBatch", batchName],
          queryFn: async () => {
            const query = buildQuery(supabase, "salerecordorm", {
              eq: { batch_name: batchName, event: "ADDED" },
            });
            const { data, error } = await query;
            if (error) throw error;
            return { batchName, sales: data || ([] as SaleRecordRow[]) };
          },
        },
        {
          queryKey: ["feedsByBatch", batchName],
          queryFn: async () => {
            const query = buildQuery(supabase, "feedrecordorm", {
              eq: { batch_name: batchName, event: "ADDED" },
            });
            const { data, error } = await query;
            if (error) throw error;
            return { batchName, feeds: data || ([] as FeedRecordRow[]) };
          },
        },
      ])
      .flat(),
  });

  // 組織批次聚合數據
  const batchAggregates = useMemo((): BatchAggregate[] => {
    // 檢查是否所有查詢都已完成
    const isAllQueriesSettled = batchQueriesResults.every(
      (query) => !query.isLoading
    );

    if (!isAllQueriesSettled) return [];

    // 按批次名稱組織資料
    const batchesMap = new Map<string, BatchAggregate>();

    // 初始化聚合結構
    batchNames.forEach((batchName) => {
      batchesMap.set(batchName, {
        batchName,
        breeds:
          breedRecords?.filter((breed) => breed.batch_name === batchName) || [],
        sales: [],
        feeds: [],
      });
    });

    // 合併銷售記錄
    batchQueriesResults.forEach((query) => {
      if (query.isSuccess && query.data) {
        const data = query.data as any;

        if ("sales" in data) {
          const batchAggregate = batchesMap.get(data.batchName);
          if (batchAggregate) {
            batchAggregate.sales = data.sales;
          }
        }

        if ("feeds" in data) {
          const batchAggregate = batchesMap.get(data.batchName);
          if (batchAggregate) {
            batchAggregate.feeds = data.feeds;
          }
        }
      }
    });

    return Array.from(batchesMap.values());
  }, [batchNames, breedRecords, batchQueriesResults]);

  // 處理品種篩選
  const handleBreedSelect = useCallback((breed: ChickenBreedType | null) => {
    setQueryOptions((prev) => {
      // 複製新的選項物件
      const newOptions = { ...prev };

      // 處理品種篩選條件
      if (!breed) {
        if (newOptions.eq) {
          newOptions.eq = { ...newOptions.eq };
          delete newOptions.eq.chicken_breed;
        }
      } else {
        newOptions.eq = { ...newOptions.eq, chicken_breed: breed };
      }

      return newOptions;
    });
  }, []);

  // 處理完成狀態篩選
  const toggleIsCompleted = useCallback(() => {
    setQueryOptions((prev) => {
      const currentState = prev.eq?.is_completed;
      const newEq = { ...prev.eq };

      // 循環切換：undefined -> true -> false -> undefined
      if (currentState === undefined) {
        newEq.is_completed = true;
      } else if (currentState === true) {
        newEq.is_completed = false;
      } else {
        // 當為false時，刪除is_completed屬性，等同於設置為undefined
        delete newEq.is_completed;
      }

      return {
        ...prev,
        eq: newEq,
      };
    });
  }, []);

  // 排序處理
  const handleSort = useCallback((column: keyof BreedRecordRow) => {
    setSortColumn(column);
    setSortDirection((prev) => (prev === "asc" ? "desc" : "asc"));
  }, []);

  // 搜尋處理
  const handleSearch = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    setSearchTerm(e.target.value);
  }, []);

  // 排序和過濾邏輯抽離為可重用的函數
  const sortAndFilterData = useCallback(
    (
      data: BreedRecordRow[],
      searchTerm: string,
      sortColumn: keyof BreedRecordRow,
      sortDirection: "asc" | "desc"
    ) => {
      let result = [...data];

      // 搜尋過濾
      if (searchTerm) {
        const searchLower = searchTerm.toLowerCase();
        result = result.filter(
          (record) =>
            record.batch_name?.toLowerCase().includes(searchLower) ||
            record.farm_name.toLowerCase().includes(searchLower) ||
            record.chicken_breed.toLowerCase().includes(searchLower)
        );
      }

      // 排序函數
      const compareValues = (
        a: any,
        b: any,
        direction: "asc" | "desc"
      ): number => {
        // 處理空值
        if (a === null || a === undefined) return direction === "asc" ? -1 : 1;
        if (b === null || b === undefined) return direction === "asc" ? 1 : -1;

        // 字串比較
        if (typeof a === "string" && typeof b === "string") {
          return direction === "asc"
            ? a.localeCompare(b, "zh-TW")
            : b.localeCompare(a, "zh-TW");
        }

        // 數字比較
        if (typeof a === "number" && typeof b === "number") {
          return direction === "asc" ? a - b : b - a;
        }

        // 布林值比較
        if (typeof a === "boolean" && typeof b === "boolean") {
          return direction === "asc"
            ? a === b
              ? 0
              : a
                ? 1
                : -1
            : a === b
              ? 0
              : a
                ? -1
                : 1;
        }

        // 日期比較
        if (
          typeof a === "string" &&
          typeof b === "string" &&
          !isNaN(Date.parse(a)) &&
          !isNaN(Date.parse(b))
        ) {
          return direction === "asc"
            ? new Date(a).getTime() - new Date(b).getTime()
            : new Date(b).getTime() - new Date(a).getTime();
        }

        return 0;
      };

      // 執行排序
      result.sort((a, b) =>
        compareValues(a[sortColumn], b[sortColumn], sortDirection)
      );

      return result;
    },
    []
  );

  // 使用memoized值產生過濾後的資料
  const filteredData = useMemo(() => {
    return sortAndFilterData(
      breedRecords || [],
      searchTerm,
      sortColumn,
      sortDirection
    );
  }, [breedRecords, searchTerm, sortColumn, sortDirection, sortAndFilterData]);

  return {
    // 數據
    data: breedRecords,
    filteredData,
    batchAggregates,
    error: error as Error | null,
    loading: isLoading,

    // 查詢參數
    queryOptions,
    sortColumn,
    sortDirection,
    searchTerm,

    // 操作方法
    fetchBreeds,
    handleBreedSelect,
    toggleIsCompleted,
    handleSort,
    handleSearch,
    setSearchTerm,
  };
};
