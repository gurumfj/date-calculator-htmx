import { useBatchStore } from "@/stores/batchStore";
import supabase from "@app-lib/supabaseClient";
import {
  BatchAggregateIndex,
  BatchAggregate,
  BreedRecordRow,
  FeedRecordRow,
  SaleRecordRow,
  CustomData,
} from "@app-types";
import { ChickenBreedType } from "@app-types";
import { useQuery, useMutation } from "@tanstack/react-query";

export interface BatchAggregateQuery {
  chickenBreed?: ChickenBreedType;
  start?: Date;
  end?: Date;
  sortOrder?: "asc" | "desc";
  isCompleted?: boolean;
}

/**
 * 獲取批次索引數據
 * @param query 批次查詢條件
 * @returns 批次索引數據和加載狀態
 */
function useBatchAggregatesIndex(query: BatchAggregateQuery): {
  data: BatchAggregateIndex[];
  isLoading: boolean;
  isError: boolean;
  error: Error | null;
} {
  const startString = query.start
    ? query.start.toISOString().split("T")[0]
    : "";
  const endString = query.end ? query.end.toISOString().split("T")[0] : "";

  const { data, isLoading, isError, error } = useQuery({
    queryKey: [
      "batchAggregates",
      query.chickenBreed,
      startString,
      endString,
      query.sortOrder,
      query.isCompleted,
    ],
    queryFn: async (): Promise<BatchAggregateIndex[]> => {
      const queryBuilder = supabase.from("batchaggregates").select("*");

      if (query.chickenBreed) {
        queryBuilder.eq("chicken_breed", query.chickenBreed);
      }

      if (query.start && query.end) {
        queryBuilder
          .gte("final_date", startString)
          .lte("initial_date", endString);
      }

      // if (query.isCompleted !== undefined) {
      //   queryBuilder.eq(
      //     "data->>batchActivity",
      //     query.isCompleted ? "completed" : "breeding"
      //   );
      // }

      if (query.sortOrder) {
        queryBuilder.order("initial_date", {
          ascending: query.sortOrder === "asc",
        });
      }

      const { data, error } = await queryBuilder;
      if (error) throw error;

      // 計算批次活動
      return data || [];
    },
  });

  return {
    data: data || [],
    isLoading,
    isError,
    error,
  };
}

/**
 * 更新指定批次的 CustomData
 * @returns mutation 物件，可用於觸發更新
 */
export function useUpdateBatchCustomData() {
  return useMutation<
    void,
    Error,
    { batchName: string; customData: CustomData }
  >({
    mutationFn: async (variables) => {
      const { batchName, customData } = variables;
      const { error } = await supabase
        .from("batchaggregates")
        .update({ data: customData })
        .eq("batch_name", batchName);

      if (error) throw error;
    },
    onSuccess: () => {
      console.log("Batch custom data updated successfully");
      // window.location.reload();
    },
    onError: (error) => {
      throw error;
    },
  });
}

/**
 * 獲取批次繁殖記錄
 * @param batchName 批次名稱
 * @returns 繁殖記錄和加載狀態
 */
function useBreedRecordsByBatchName(batchName: string | null): {
  data: BreedRecordRow[];
  isLoading: boolean;
  isError: boolean;
  error: Error | null;
} {
  const { data, isLoading, isError, error } = useQuery({
    queryKey: ["breedRecords", batchName],
    queryFn: async () => {
      if (!batchName) return [];
      const { data, error } = await supabase
        .from("breedrecordorm")
        .select("*")
        .eq("batch_name", batchName)
        .eq("event", "ADDED");
      if (error) throw error;
      return data || [];
    },
    enabled: !!batchName,
  });

  return {
    data: data || [],
    isLoading,
    isError,
    error,
  };
}

/**
 * 獲取批次銷售記錄
 * @param batchName 批次名稱
 * @returns 銷售記錄和加載狀態
 */
function useSaleRecordsByBatchName(batchName: string | null): {
  data: SaleRecordRow[];
  isLoading: boolean;
  isError: boolean;
  error: Error | null;
} {
  const { data, isLoading, isError, error } = useQuery({
    queryKey: ["saleRecords", batchName],
    queryFn: async () => {
      if (!batchName) return [];
      const { data, error } = await supabase
        .from("salerecordorm")
        .select("*")
        .eq("batch_name", batchName)
        .eq("event", "ADDED");
      if (error) throw error;
      return data || [];
    },
    enabled: !!batchName,
  });

  return {
    data: data || [],
    isLoading,
    isError,
    error,
  };
}

/**
 * 獲取批次飼料記錄
 * @param batchName 批次名稱
 * @returns 飼料記錄和加載狀態
 */
function useFeedRecordsByBatchName(batchName: string | null): {
  data: FeedRecordRow[];
  isLoading: boolean;
  isError: boolean;
  error: Error | null;
} {
  const { data, isLoading, isError, error } = useQuery({
    queryKey: ["feedRecords", batchName],
    queryFn: async () => {
      if (!batchName) return [];
      const { data, error } = await supabase
        .from("feedrecordorm")
        .select("*")
        .eq("batch_name", batchName)
        .eq("event", "ADDED");
      if (error) throw error;
      return data || [];
    },
    enabled: !!batchName,
  });

  return {
    data: data || [],
    isLoading,
    isError,
    error,
  };
}

/**
 * 獲取單個批次完整資料的 Hook
 * @param batchName 批次名稱
 * @returns 單個批次的聚合數據
 */
function useBatchAggregate(batchName: string | null): BatchAggregate | null {
  // 只在有批次名稱時才獲取資料
  const batchStore = useBatchStore();

  // 如果 store 中沒有找到，就直接查詢
  const { data: batchIndices, isLoading: isLoadingIndex } = useQuery({
    queryKey: ["batchIndex", batchName],
    queryFn: async () => {
      if (!batchName) return [];
      const foundIndex = batchStore.batchIndices.find(
        (b) => b.batch_name === batchName
      );

      if (foundIndex) return [foundIndex];

      const { data, error } = await supabase
        .from("batchaggregates")
        .select("*")
        .eq("batch_name", batchName);
      if (error) throw error;
      return data || [];
    },
    enabled: !!batchName,
  });

  // 使用 React Query hooks 獲取詳細記錄
  const { data: breeds, isLoading: isLoadingBreeds } =
    useBreedRecordsByBatchName(batchName);

  const { data: sales, isLoading: isLoadingSales } =
    useSaleRecordsByBatchName(batchName);

  const { data: feeds, isLoading: isLoadingFeeds } =
    useFeedRecordsByBatchName(batchName);

  // 如果正在加載或沒有批次名稱或找不到批次索引，返回 null
  if (
    isLoadingIndex ||
    isLoadingBreeds ||
    isLoadingSales ||
    isLoadingFeeds ||
    !batchName ||
    !batchIndices ||
    batchIndices.length === 0
  ) {
    return null;
  }

  const calculateActivity = () => {
    if (batchIndices[0].data?.batchActivity) {
      return batchIndices[0].data.batchActivity;
    }
    if (breeds[0]?.is_completed) {
      return "completed";
    }
    {
      if (sales.length > 0) {
        return "selling";
      }
      return "breeding";
    }
  };

  const customData: CustomData = {
    ...batchIndices[0].data,
    batchActivity: calculateActivity(),
  };
  // console.log(customData);

  // 組合成 BatchAggregate 並返回
  return {
    batchIndex: batchIndices[0],
    customData: customData,
    breeds: breeds || [],
    sales: sales || [],
    feeds: feeds || [],
    batchName: batchName,
  };
}

export { useBatchAggregatesIndex, useBatchAggregate };
