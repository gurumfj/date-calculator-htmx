import { useMemo } from "react";
import { useQueries } from "@tanstack/react-query";
import supabase from "@app-lib/supabaseClient";
import { buildQuery } from "@hooks/supabase/queryBuilder";
import { SaleRecordRow, FeedRecordRow } from "@app-types";
import { QueryOptions } from "@hooks/supabase/types";

/**
 * Custom Hook: 根據批次名稱列表，使用 useQueries 平行取得銷售和飼料紀錄。
 * @param batchNames - 批次名稱陣列
 * @returns 包含 salesByBatch, feedsByBatch, isSubQueryLoading, subQueryError 的物件
 */
export const useBatchDetailsQueries = (batchNames: string[]) => {
  // 準備 useQueries 的查詢物件陣列
  const salesFeedQueries = useMemo(() => {
    if (batchNames.length === 0) return [];
    return batchNames.flatMap((batchName) => [
      // Sales query
      {
        queryKey: ["sales", batchName],
        queryFn: async () => {
          const { data, error } = await buildQuery(supabase, "salerecordorm", {
            eq: { batch_name: batchName, event: "ADDED" },
          } as QueryOptions);
          if (error) throw error;
          return (data as SaleRecordRow[]) || [];
        },
        staleTime: 300000, // 5 mins cache
      },
      // Feeds query
      {
        queryKey: ["feeds", batchName],
        queryFn: async () => {
          const { data, error } = await buildQuery(supabase, "feedrecordorm", {
            eq: { batch_name: batchName, event: "ADDED" },
          } as QueryOptions);
          if (error) throw error;
          return (data as FeedRecordRow[]) || [];
        },
        staleTime: 300000, // 5 mins cache
      },
    ]);
  }, [batchNames]);

  // 執行 useQueries
  const results = useQueries({ queries: salesFeedQueries });

  // 處理 useQueries 的結果
  const queryResults = useMemo(() => {
    const sales: { [key: string]: SaleRecordRow[] } = {};
    const feeds: { [key: string]: FeedRecordRow[] } = {};
    let isLoading = false;
    let firstError: Error | null = null;

    results.forEach((result, index) => {
      const queryKey = salesFeedQueries[index]?.queryKey;
      if (!queryKey) return;
      const type = queryKey[0];
      const batchName = queryKey[1] as string;

      if (result.isLoading) isLoading = true;
      if (result.error && !firstError) firstError = result.error as Error;
      if (result.data) {
        if (type === "sales") {
          sales[batchName] = result.data as SaleRecordRow[];
        } else if (type === "feeds") {
          feeds[batchName] = result.data as FeedRecordRow[];
        }
      }
    });

    return {
      salesByBatch: sales,
      feedsByBatch: feeds,
      isSubQueryLoading: isLoading,
      subQueryError: firstError,
    };
  }, [results, salesFeedQueries]);

  return queryResults;
};
