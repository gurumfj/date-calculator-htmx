import {
  BatchAggregateIndex,
  BatchAggregateWithRows,
  CustomData,
} from "@/types";
import { BatchFilters } from "../types";
import supabase from "@app-lib/supabaseClient";
import { format } from "date-fns";
import { useMutation, useQuery } from "@tanstack/react-query";

// 將批次索引查詢封裝為獨立函數，方便 hook 與其他服務複用
// 這樣設計可集中維護查詢條件，減少重複邏輯
async function fetchBatchAggregatesIndex(
  filter: BatchFilters
): Promise<{ data: BatchAggregateIndex[]; error: Error | null }> {
  const queryBuilder = supabase.from("batchaggregates").select("*");

  if (filter.filterByBreed) {
    // 預設以品種作為主要篩選條件，符合實際業務需求
    queryBuilder.eq("chicken_breed", filter.filterByBreed);
  }

  if (filter.filterByStart && filter.filterByEnd) {
    // 查詢區間設計為 final_date >= start, initial_date <= end
    // 這樣可支援跨月/跨批次查詢，並與資料表結構對齊
    queryBuilder
      .gte("final_date", format(filter.filterByStart, "yyyy-MM-dd"))
      .lte("initial_date", format(filter.filterByEnd, "yyyy-MM-dd"));
  }

  if (filter.filterByActivity.length > 0) {
    // 支援多活動狀態篩選，使用 or 組合查詢
    // 這樣可讓用戶同時查詢多種批次狀態，提升彈性
    queryBuilder.or(
      filter.filterByActivity
        .map((activity) => `data->>batchActivity=="${activity}"`)
        .join(",")
    );
  }

  if (filter.sortOrder) {
    // 預設以初始日期排序，方便時間軸展示
    queryBuilder.order("initial_date", {
      ascending: filter.sortOrder === "asc",
    });
  }

  const { data, error } = await queryBuilder;
  if (error) throw error; // 直接拋出錯誤，讓呼叫方統一處理
  return { data: data || [], error: null };
}

// 封裝為 React Query hook，方便組件直接取得批次索引資料與 loading/error 狀態
// queryKey 設計細緻，確保不同條件下快取不互相覆蓋
export function useFetchBatchAggregatesIndex(filter: BatchFilters) {
  return useQuery({
    queryKey: [
      "batchAggregatesIndex",
      filter.filterByBreed,
      filter.filterByStart ? format(filter.filterByStart, "yyyy-MM-dd") : null,
      filter.filterByEnd ? format(filter.filterByEnd, "yyyy-MM-dd") : null,
      filter.filterByActivity,
      filter.sortOrder,
    ],
    queryFn: async () => {
      const { data, error } = await fetchBatchAggregatesIndex(filter);
      if (error) throw error;
      return data || [];
    },
  });
}

async function fetchBatchIndex(
  batchName: string
): Promise<BatchAggregateIndex | null> {
  const { data, error } = await supabase
    .from("batchaggregates")
    .select("*")
    .eq("batch_name", batchName)
    .single();

  if (error) throw error;
  return data || null;
}

// 封裝銷售記錄查詢，集中管理 event 過濾，避免組件重複實作
// 僅查詢 ADDED 事件，確保資料正確性與一致性
async function fetchSalesRecordsByBatchName(batchName: string) {
  const { data, error } = await supabase
    .from("salerecordorm")
    .select("*")
    .eq("batch_name", batchName)
    .eq("event", "ADDED");
  if (error) throw error;
  return data || [];
}

// 封裝飼料記錄查詢，統一 event 過濾，方便日後擴充
// 僅查詢 ADDED 事件，排除異動與刪除紀錄
async function fetchFeedRecordsByBatchName(batchName: string) {
  const { data, error } = await supabase
    .from("feedrecordorm")
    .select("*")
    .eq("batch_name", batchName)
    .eq("event", "ADDED");
  if (error) throw error;
  return data || [];
}

// 封裝繁殖記錄查詢，統一 event 過濾，確保資料一致性
// 僅查詢 ADDED 事件，排除異動與刪除紀錄
async function fetchBreedRecordsByBatchName(batchName: string) {
  const { data, error } = await supabase
    .from("breedrecordorm")
    .select("*")
    .eq("batch_name", batchName)
    .eq("event", "ADDED");
  if (error) throw error;
  return data || [];
}

// 封裝單一批次聚合查詢，並行查詢所有關聯資料，提升效能
// 統一回傳格式，方便組件直接消費並減少重複組裝
export function useFetchBatchAggregates(batchName: string) {
  return useQuery<BatchAggregateWithRows | null>({
    queryKey: ["batchAggregates", batchName],
    // 查詢指定批次的所有關聯資料
    queryFn: async () => {
      if (!batchName) return null;
      // 並行取得所有資料，提升資料同步效率
      const [batch, breeds, feeds, sales] = await Promise.all([
        fetchBatchIndex(batchName),
        fetchBreedRecordsByBatchName(batchName),
        fetchFeedRecordsByBatchName(batchName),
        fetchSalesRecordsByBatchName(batchName),
      ]);
      // 若查無批次則回傳 null，避免組件誤用空資料
      if (!batch || !Array.isArray(batch) || batch.length === 0) return null;

      // 根據資料優先級推斷 batchActivity 狀態，確保 UI 準確反映批次真實狀態
      const batchActivity =
        batch[0].data?.batchActivity ||
        (breeds.length > 0 && breeds[0].is_completed === true
          ? "completed"
          : sales.length > 0
            ? "selling"
            : "breeding");

      // 返回標準化的數據，方便上層組件直接消費
      return {
        index: { ...batch[0], data: { ...batch[0].data, batchActivity } },
        breeds: breeds || [],
        feeds: feeds || [],
        sales: sales || [],
      };
    },
  });
}

/**
 * 更新指定批次的 CustomData
 * @returns mutation 物件，可用於觸發更新
 */
// 將批次自訂資料更新封裝為 mutation hook，方便表單/操作直接呼叫
// 這樣做可以集中錯誤處理與 side effect，提升一致性
export function useUpdateBatchCustomData() {
  return useMutation<
    void,
    Error,
    { batchName: string; customData: CustomData }
  >({
    mutationFn: async (variables) => {
      const { batchName, customData } = variables;
      // 直接更新 supabase，確保資料一致性
      const { error } = await supabase
        .from("batchaggregates")
        .update({ data: customData })
        .eq("batch_name", batchName);

      if (error) throw error;
    },
    onSuccess: () => {
      // 成功時可根據需求觸發全域提示或自動刷新
      console.log("Batch custom data updated successfully");
      // window.location.reload(); // 避免全頁刷新，建議用狀態同步
    },
    onError: (error) => {
      // 集中錯誤處理，方便後續接入全域錯誤提示
      throw error;
    },
  });
}
